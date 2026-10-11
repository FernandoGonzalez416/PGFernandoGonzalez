"""Pronóstico recursivo a 7 días, compartido entre evaluación y producción (M1-BIS).

Ambos caminos usan esta misma función: la evaluación por bloques la invoca
desde cada origen de bloque y la producción desde el último día conocido.
"""

import numpy as np


HORIZONTE = 7


def pronosticar_recursivo(
    modelo,
    X_ultimo: np.ndarray,
    serie_hist: np.ndarray,
    horizonte: int = HORIZONTE,
) -> np.ndarray:
    """
    Pronóstico recursivo a 7 días.

    Cada día pronosticado alimenta los lags y medias del siguiente.
    X_ultimo: features del día origen (shape: (1, n_features) o (n_features,))
    serie_hist: serie histórica de unidades hasta el día anterior al origen
        (para calcular lags/medias iniciales; nunca incluye el bloque a pronosticar)
    """
    # El modelo llega ya entrenado (quien llama lo ajusta solo con filas
    # anteriores al origen). NO reajustarlo aquí: ajustarlo con una sola muestra
    # colapsa los árboles a una hoja y el pronóstico sale plano (= último valor).

    # Para el pronóstico recursivo, necesitamos simular la evolución de features
    # Simplificación: usamos el último estado conocido y actualizamos lags/medias
    # con cada predicción

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

        # El modelo NO se reentrena dentro del horizonte: se usa el ya entrenado
        # y solo se actualizan las features (lags, medias) con cada predicción.

    return np.array(predicciones)
