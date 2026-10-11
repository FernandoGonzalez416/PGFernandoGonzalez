"""Pronóstico recursivo a 7 días y intervalo aproximado."""

import numpy as np
from sklearn.base import clone

from .modelos import crear_modelos, nombre_metodo_clave_a_bd
from .evaluacion import ResultadoEvaluacion, MetricasValidacion


HORIZONTE = 7
FACTOR_INTERVALO = 1.28  # ~80% para distribución normal


def pronosticar_recursivo(
    modelo,
    X_ultimo: np.ndarray,
    serie_hist: np.ndarray,
    horizonte: int = HORIZONTE,
) -> np.ndarray:
    """
    Pronóstico recursivo a 7 días.

    Cada día pronosticado alimenta los lags y medias del siguiente.
    X_ultimo: features del último día conocido (shape: (1, n_features))
    serie_hist: serie histórica completa de unidades (para calcular lags/medias iniciales)
    """
    # Clonar modelo para no modificar el original
    modelo = clone(modelo)
    modelo.fit(X_ultimo.reshape(1, -1) if X_ultimo.ndim == 1 else X_ultimo, 
               serie_hist[-1:] if len(serie_hist) > 0 else np.array([0.0]))

    # Para el pronóstico recursivo, necesitamos simular la evolución de features
    # Simplificación: usamos el último estado conocido y actualizamos lags/medias
    # con cada predicción

    n_features = X_ultimo.shape[0] if X_ultimo.ndim == 1 else X_ultimo.shape[1]
    predicciones = []

    # Estado mutable para features
    features_actual = X_ultimo.copy() if X_ultimo.ndim == 1 else X_ultimo[-1].copy()
    historial_ventanas = list(serie_hist[-7:]) if len(serie_hist) >= 7 else list(serie_hist)

    for _ in range(horizonte):
        # Predecir siguiente día
        pred = modelo.predict(features_actual.reshape(1, -1))[0]
        pred = max(0.0, pred)  # truncar negativos
        predicciones.append(pred)

        # Actualizar features para siguiente iteración
        # Índices: 0=dow, 1=mes, 2=fin_semana, 3=tendencia, 4=lag1, 5=lag7, 6=media_7, 7=desv_7
        # dow, mes, fin_semana, tendencia: no cambian en simulación simple
        # o bien: asumimos que avanzamos un día
        features_actual[3] += 1  # tendencia +1
        # dow y fin_semana: rotar (simplificado)
        dow = int(features_actual[0])
        features_actual[0] = (dow + 1) % 7
        features_actual[2] = 1 if features_actual[0] >= 5 else 0

        # lag1 <- predicción actual
        features_actual[4] = pred

        # lag7: valor de hace 7 días (del historial o predicciones previas)
        if len(historial_ventanas) >= 7:
            features_actual[5] = historial_ventanas[-7]
        elif len(predicciones) >= 7:
            features_actual[5] = predicciones[-7]
        else:
            features_actual[5] = 0.0

        # Actualizar ventana de 7 días
        historial_ventanas.append(pred)
        if len(historial_ventanas) > 7:
            historial_ventanas.pop(0)

        # Recalcular media y desv móvil 7
        if len(historial_ventanas) > 0:
            features_actual[6] = float(np.mean(historial_ventanas))
            features_actual[7] = float(np.std(historial_ventanas, ddof=0))

        # Re-entrenar modelo con dato nuevo (simplificado: solo agregamos al historial)
        # En producción se reentrenaría completo; aquí actualizamos incrementalmente
        # Para Random Forest no hay partial_fit, así que reentrenamos con todo
        # Como es costoso, en esta versión simplificada solo actualizamos features
        # y usamos el modelo ya entrenado

    return np.array(predicciones)


def calcular_intervalo(
    demanda_pronosticada: float,
    mae_diario: float,
    horizonte: int = HORIZONTE,
) -> Tuple[float, float]:
    """
    Intervalo aproximado [D - m, D + m] con m = 1.28 * MAE_diario * sqrt(7).

    NOTA: Esta es una APROXIMACIÓN, no un intervalo estadístico exacto.
    Asume errores independientes e idénticamente distribuidos.
    """
    m = FACTOR_INTERVALO * mae_diario * np.sqrt(horizonte)
    inf = max(0.0, demanda_pronosticada - m)
    sup = demanda_pronosticada + m
    return inf, sup


def generar_pronostico_completo(
    resultado_eval: ResultadoEvaluacion,
    X: np.ndarray,
    y: np.ndarray,
    serie_completa: np.ndarray,
) -> Tuple[np.ndarray, float, float, float, float, float]:
    """
    Genera pronóstico final de 7 días usando el modelo seleccionado.

    Returns:
        (pronostico_7dias, demanda_total, intervalo_inf, intervalo_sup,
         mae_validacion, wape_validacion)
    """
    modelos = crear_modelos()
    clave_modelo = None
    for k, v in modelos.items():
        if nombre_metodo_clave_a_bd(k) == resultado_eval.modelo_seleccionado:
            clave_modelo = k
            break

    if resultado_eval.modelo_seleccionado == "promedio_movil":
        # Línea base: promedio móvil de 7 días plano
        ultimos_7 = serie_completa[-7:] if len(serie_completa) >= 7 else serie_completa
        promedio = float(np.mean(ultimos_7)) if len(ultimos_7) > 0 else 0.0
        pronostico = np.full(HORIZONTE, max(0.0, promedio))
        demanda_total = float(np.sum(pronostico))
        mae_val = resultado_eval.metricas_modelo.mae
        wape_val = resultado_eval.metricas_modelo.wape
        inf, sup = calcular_intervalo(demanda_total, mae_val)
        return pronostico, demanda_total, inf, sup, mae_val, wape_val

    # Modelo ML: reentrenar con TODOS los datos y pronosticar recursivo
    modelo = modelos[clave_modelo]
    modelo.fit(X, y)

    # Features del último día válido
    X_ultimo = X[-1]

    pronostico = pronosticar_recursivo(modelo, X_ultimo, serie_completa, HORIZONTE)
    demanda_total = float(np.sum(pronostico))
    mae_val = resultado_eval.metricas_modelo.mae
    wape_val = resultado_eval.metricas_modelo.wape
    inf, sup = calcular_intervalo(demanda_total, mae_val)

    return pronostico, demanda_total, inf, sup, mae_val, wape_val