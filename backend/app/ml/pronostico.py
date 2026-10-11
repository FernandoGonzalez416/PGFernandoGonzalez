"""Pronóstico recursivo a 7 días y intervalo aproximado."""

import numpy as np

from .modelos import crear_modelos, nombre_metodo_clave_a_bd
from .evaluacion import ResultadoEvaluacion, MetricasValidacion
from .recursivo import HORIZONTE, pronosticar_recursivo


FACTOR_INTERVALO = 1.28  # ~80% para distribución normal


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