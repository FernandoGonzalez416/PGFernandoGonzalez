"""Evaluación y selección de modelos (validación temporal, suficiencia P13)."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics import mean_absolute_error

from .modelos import crear_modelos, nombre_metodo_clave_a_bd
from .features import WARMUP_DIAS
from .recursivo import HORIZONTE, pronosticar_recursivo


# Umbrales configurables (P13)
VENTANA_MINIMA_DIAS = 75
DIAS_CON_VENTA_ENTRENAMIENTO_MIN = 20
DIAS_CON_VENTA_VALIDACION_MIN = 3
VALIDACION_DIAS = 14
# Orígenes rodantes para la evaluación semanal (M1-TER): los últimos 7 días
# de la ventana de validación como primer día de cada semana pronosticada
ORIGENES_RODANTES = 8


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
    Calcula MAE, WAPE y nMAE sobre DEMANDA SEMANAL ACUMULADA (M1-TER).

    Cada elemento de y_real / y_pred es el total de una semana de 7 días.
    MAE_semanal: unidades por semana. WAPE_semanal = suma|error| / suma real.
    nMAE = MAE_semanal / demanda semanal media.
    """
    mae = float(mean_absolute_error(y_real, y_pred))

    total_real = float(np.sum(y_real))
    if total_real > 0:
        wape = float(np.sum(np.abs(y_real - y_pred)) / total_real)
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
    Evaluación semanal acumulada con orígenes rodantes (M1-TER).

    El modelo se entrena UNA vez con las filas anteriores a la ventana de
    validación. Para cada uno de los 8 orígenes (n-14 ... n-7 en filas de
    validación): pronóstico recursivo de 7 días con la serie real hasta o-1
    (función compartida de producción) y suma de esos 7 días; se compara con
    la suma real de [o, o+6]. Devuelve los 8 totales pronosticados y reales.
    """
    n_val = len(y_val)
    if n_val != VALIDACION_DIAS or len(serie_hist_completa) == 0:
        # Sin los 14 días exactos o sin serie: evaluación simple de un paso
        modelo.fit(X_train, y_train)
        return modelo.predict(X_val), y_val

    # Origen del primer día de validación en coordenadas de la serie completa
    origen_serie_val = WARMUP_DIAS + len(X_train)

    modelo.fit(X_train, y_train)
    totales_pred, totales_real = [], []
    for o in range(ORIGENES_RODANTES):
        origen = origen_serie_val + (VALIDACION_DIAS - HORIZONTE - o)
        pred_7 = pronosticar_recursivo(
            modelo, X_val[VALIDACION_DIAS - HORIZONTE - o], serie_hist_completa[:origen], HORIZONTE
        )
        totales_pred.append(float(np.sum(pred_7)))
        totales_real.append(float(np.sum(serie_hist_completa[origen : origen + HORIZONTE])))

    y_pred = np.array(totales_pred, dtype=np.float64)
    y_real = np.array(totales_real, dtype=np.float64)
    return y_pred, y_real


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
    Sobre esa ventana, 8 orígenes rodantes (o = n-14 ... n-7): cada origen se
    pronostica de forma recursiva con el mismo procedimiento de producción
    (sin usar valores reales del bloque) y se compara el total semanal.
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
        base_b1 = pronosticar_promedio_movil_7(serie_completa[:idx_serie_val], HORIZONTE)
        base_b2 = pronosticar_promedio_movil_7(
            serie_completa[: idx_serie_val + HORIZONTE], HORIZONTE
        )
        y_pred_base = np.concatenate([base_b1, base_b2])
        totales_base = np.array(
            [float(np.sum(y_pred_base[:7])), float(np.sum(y_pred_base[7:]))]
        )
        totales_real_insuf = np.array(
            [
                float(np.sum(serie_completa[idx_serie_val : idx_serie_val + 7])),
                float(np.sum(serie_completa[idx_serie_val + 7 : idx_serie_val + 14])),
            ]
        )
        mae_b, wape_b, nmae_b = calcular_metricas(totales_real_insuf, totales_base)
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
        totales_pred, totales_real = evaluar_por_bloques_recursivos(
            modelo, X_train, y_train, X_val, y_val, serie_completa
        )
        mae, wape, nmae = calcular_metricas(totales_real, totales_pred)

        if mae < mejor_mae:
            mejor_mae = mae
            mejor_clave = clave
            mejor_metricas = MetricasValidacion(
                mae, wape, nmae, dias_venta_val, float(np.mean(totales_real))
            )

    # Línea base por origen: media móvil plana de 7 días tomada en cada origen
    base_totales, reales_base = [], []
    for o in range(ORIGENES_RODANTES):
        origen = idx_serie_val + (len(y_val) - HORIZONTE - o)
        base_totales.append(
            float(np.sum(pronosticar_promedio_movil_7(serie_completa[:origen], HORIZONTE)))
        )
        reales_base.append(float(np.sum(serie_completa[origen : origen + HORIZONTE])))
    base_totales = np.array(base_totales, dtype=np.float64)
    totales_real_base = np.array(reales_base, dtype=np.float64)
    mae_base, wape_base, nmae_base = calcular_metricas(totales_real_base, base_totales)
    metricas_base = MetricasValidacion(
        mae_base, wape_base, nmae_base, dias_venta_val, float(np.mean(totales_real_base))
    )

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