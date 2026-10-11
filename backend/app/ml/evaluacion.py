"""Evaluación y selección de modelos (validación temporal, suficiencia P13)."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import mean_absolute_error

from .modelos import crear_modelos, nombre_metodo_clave_a_bd


# Umbrales configurables (P13)
VENTANA_MINIMA_DIAS = 75
DIAS_CON_VENTA_ENTRENAMIENTO_MIN = 20
DIAS_CON_VENTA_VALIDACION_MIN = 3
VALIDACION_DIAS = 14


@dataclass
class MetricasValidacion:
    mae: float
    wape: float
    nmae: float
    dias_con_venta_validacion: int
    demanda_media_diaria: float


@dataclass
class ResultadoEvaluacion:
    modelo_seleccionado: str
    metricas_modelo: MetricasValidacion
    metricas_linea_base: MetricasValidacion
    suficiente: bool
    motivo_no_suficiente: Optional[str]
    observaciones_usadas: int


def calcular_metricas(
    y_real: np.ndarray,
    y_pred: np.ndarray,
) -> Tuple[float, float, float]:
    """
    Calcula MAE, WAPE y nMAE.

    WAPE: solo sobre días con venta real > 0
    nMAE: MAE / demanda_media_diaria (sobre todo el periodo de validación)
    """
    mae = float(mean_absolute_error(y_real, y_pred))

    # WAPE: solo días con venta > 0
    mask_venta = y_real > 0
    if np.any(mask_venta):
        wape = float(np.sum(np.abs(y_real[mask_venta] - y_pred[mask_venta])) / np.sum(y_real[mask_venta]))
    else:
        wape = 0.0

    demanda_media = float(np.mean(y_real))
    nmae = mae / demanda_media if demanda_media > 0 else 0.0

    return mae, wape, nmae


def pronosticar_promedio_movil_7(serie_hist: np.ndarray, horizonte: int = 7) -> np.ndarray:
    """
    Línea base: promedio móvil simple de 7 días, pronóstico plano.
    Usa los últimos 7 días disponibles del historial de ENTRENAMIENTO.
    """
    ultimos_7 = serie_hist[-7:] if len(serie_hist) >= 7 else serie_hist
    promedio = float(np.mean(ultimos_7)) if len(ultimos_7) > 0 else 0.0
    return np.full(horizonte, max(0.0, promedio))


def evaluar_por_bloques_recursivos(
    modelo,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    serie_hist_completa: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Evaluación por bloques de 7 días con procedimiento recursivo.

    Simula cómo opera el pronóstico real: reentrena con datos hasta t-1
    y pronostica 7 días, luego avanza 7 días y repite.

    Para validación de 14 días = 2 bloques de 7 días.

    Returns:
        y_pred_bloques: predicciones para los 14 días de validación
        y_real_bloques: valores reales correspondientes
    """
    n_val = len(y_val)
    if n_val != VALIDACION_DIAS:
        # Si no son exactamente 14 días, evaluación simple
        modelo.fit(X_train, y_train)
        return modelo.predict(X_val), y_val

    # Bloque 1: días 0-6 de validación
    modelo.fit(X_train, y_train)
    pred_bloque1 = modelo.predict(X_val[:7])

    # Bloque 2: días 7-13 de validación
    X_train_b2 = np.vstack([X_train, X_val[:7]])
    y_train_b2 = np.concatenate([y_train, y_val[:7]])
    modelo.fit(X_train_b2, y_train_b2)
    pred_bloque2 = modelo.predict(X_val[7:14])

    y_pred = np.concatenate([pred_bloque1, pred_bloque2])
    return y_pred, y_val


def evaluar_suficiencia(
    serie_completa: np.ndarray,
    fechas_completas: List,
    idx_inicio_validacion: int,
) -> Tuple[bool, Optional[str], int, int]:
    """
    Verifica criterio de suficiencia P13.

    Returns:
        (es_suficiente, motivo_si_no, dias_con_venta_entrenamiento, dias_con_venta_validacion)
    """
    n_dias_totales = idx_inicio_validacion
    if n_dias_totales < VENTANA_MINIMA_DIAS:
        return False, f"historial menor a {VENTANA_MINIMA_DIAS} días", 0, 0

    y_entrenamiento = serie_completa[14:idx_inicio_validacion]
    dias_con_venta_ent = int(np.sum(y_entrenamiento > 0))

    y_validacion = serie_completa[idx_inicio_validacion:]
    dias_con_venta_val = int(np.sum(y_validacion > 0))

    if dias_con_venta_ent < DIAS_CON_VENTA_ENTRENAMIENTO_MIN:
        return False, f"pocos días con venta en entrenamiento ({dias_con_venta_ent} < {DIAS_CON_VENTA_ENTRENAMIENTO_MIN})", dias_con_venta_ent, dias_con_venta_val

    if dias_con_venta_val < DIAS_CON_VENTA_VALIDACION_MIN:
        return False, f"pocos días con venta en validación ({dias_con_venta_val} < {DIAS_CON_VENTA_VALIDACION_MIN})", dias_con_venta_ent, dias_con_venta_val

    return True, None, dias_con_venta_ent, dias_con_venta_val


def evaluar_modelos(
    X: np.ndarray,
    y: np.ndarray,
    serie_completa: np.ndarray,
    fechas_completas: List,
) -> ResultadoEvaluacion:
    """
    Evalúa todos los candidatos contra la línea base y selecciona el mejor.

    División temporal: últimos 14 días = validación, resto = entrenamiento.
    """
    n = len(y)
    idx_val_inicio = n - VALIDACION_DIAS

    if idx_val_inicio <= 0:
        return ResultadoEvaluacion(
            modelo_seleccionado="promedio_movil",
            metricas_modelo=MetricasValidacion(0, 0, 0, 0, 0),
            metricas_linea_base=MetricasValidacion(0, 0, 0, 0, 0),
            suficiente=False,
            motivo_no_suficiente="datos insuficientes para validación",
            observaciones_usadas=n,
        )

    X_train, X_val = X[:idx_val_inicio], X[idx_val_inicio:]
    y_train, y_val = y[:idx_val_inicio], y[idx_val_inicio:]

    idx_serie_val = 14 + idx_val_inicio
    suficiente, motivo, dias_venta_ent, dias_venta_val = evaluar_suficiencia(
        serie_completa, fechas_completas, idx_serie_val
    )

    if not suficiente:
        y_pred_base = pronosticar_promedio_movil_7(
            serie_completa[:idx_serie_val], VALIDACION_DIAS
        )
        mae_b, wape_b, nmae_b = calcular_metricas(y_val, y_pred_base)
        return ResultadoEvaluacion(
            modelo_seleccionado="promedio_movil",
            metricas_modelo=MetricasValidacion(mae_b, wape_b, nmae_b, dias_venta_val, float(np.mean(y_val))),
            metricas_linea_base=MetricasValidacion(mae_b, wape_b, nmae_b, dias_venta_val, float(np.mean(y_val))),
            suficiente=False,
            motivo_no_suficiente=motivo,
            observaciones_usadas=len(y_train),
        )

    modelos = crear_modelos()
    mejor_mae = float("inf")
    mejor_clave = None
    mejor_metricas = None

    for clave, modelo in modelos.items():
        y_pred, _ = evaluar_por_bloques_recursivos(
            modelo, X_train, y_train, X_val, y_val, serie_completa
        )
        mae, wape, nmae = calcular_metricas(y_val, y_pred)

        if mae < mejor_mae:
            mejor_mae = mae
            mejor_clave = clave
            mejor_metricas = MetricasValidacion(mae, wape, nmae, dias_venta_val, float(np.mean(y_val)))

    y_pred_base = pronosticar_promedio_movil_7(serie_completa[:idx_serie_val], VALIDACION_DIAS)
    mae_base, wape_base, nmae_base = calcular_metricas(y_val, y_pred_base)
    metricas_base = MetricasValidacion(mae_base, wape_base, nmae_base, dias_venta_val, float(np.mean(y_val)))

    if mejor_mae < mae_base:
        return ResultadoEvaluacion(
            modelo_seleccionado=nombre_metodo_clave_a_bd(mejor_clave),
            metricas_modelo=mejor_metricas,
            metricas_linea_base=metricas_base,
            suficiente=True,
            motivo_no_suficiente=None,
            observaciones_usadas=len(y_train),
        )
    else:
        return ResultadoEvaluacion(
            modelo_seleccionado="promedio_movil",
            metricas_modelo=metricas_base,
            metricas_linea_base=metricas_base,
            suficiente=True,
            motivo_no_suficiente="el modelo no supera a la línea base",
            observaciones_usadas=len(y_train),
        )