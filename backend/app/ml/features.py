"""Construcción de features para el modelo de predicción (sin fuga de información)."""

from datetime import date
from typing import List, Tuple

import numpy as np


WARMUP_DIAS = 14


def construir_features(
    serie: np.ndarray,
    fechas: List[date],
) -> Tuple[np.ndarray, np.ndarray, List[date]]:
    """
    Construye matriz de features X y vector objetivo y a partir de la serie temporal.

    Features por día t (índice en la serie completa):
    - dow: día de la semana (0-6, lunes=0)
    - mes: mes (1-12)
    - fin_semana: 1 si sábado/domingo, 0 otherwise
    - tendencia: índice del día desde el inicio (0, 1, 2, ...)
    - lag1: venta en t-1
    - lag7: venta en t-7
    - media_movil_7: media de t-7 a t-1 (solo histórico)
    - desv_movil_7: desviación estándar de t-7 a t-1

    IMPORTANTE: Todas las features móviles y lags usan SOLO datos hasta t-1
    (nunca el valor de t ni del futuro). Se descartan los primeros WARMUP_DIAS
    filas para que todas las features estén completas.

    Retorna:
    - X: matriz (n_samples, n_features) con features para días válidos
    - y: vector objetivo (unidades en día t) para días válidos
    - fechas_validas: fechas correspondientes a cada fila de X/y
    """
    n = len(serie)
    if n <= WARMUP_DIAS:
        return np.empty((0, 8)), np.empty(0), []

    # Pre-calcular lags y medias móviles usando SOLO histórico
    lag1 = np.full(n, np.nan)
    lag7 = np.full(n, np.nan)
    media_movil_7 = np.full(n, np.nan)
    desv_movil_7 = np.full(n, np.nan)

    for i in range(n):
        # lag1: valor en t-1
        if i - 1 >= 0:
            lag1[i] = serie[i - 1]

        # lag7: valor en t-7
        if i - 7 >= 0:
            lag7[i] = serie[i - 7]

        # media móvil y desviación de 7 días: ventana [t-7, t-1]
        if i >= 7:
            ventana = serie[i - 7:i]
            media_movil_7[i] = float(np.mean(ventana))
            desv_movil_7[i] = float(np.std(ventana, ddof=0))  # poblacional

    # Construir features para días válidos (después de warmup)
    indices_validos = list(range(WARMUP_DIAS, n))
    n_validos = len(indices_validos)

    X = np.zeros((n_validos, 8), dtype=np.float64)
    y = np.zeros(n_validos, dtype=np.float64)
    fechas_validas = []

    for idx, i in enumerate(indices_validos):
        f = fechas[i]
        X[idx, 0] = f.weekday()          # dow
        X[idx, 1] = f.month              # mes
        X[idx, 2] = 1 if f.weekday() >= 5 else 0  # fin_semana
        X[idx, 3] = float(i)             # tendencia (índice día)
        X[idx, 4] = lag1[i]              # lag1
        X[idx, 5] = lag7[i]              # lag7
        X[idx, 6] = media_movil_7[i]     # media_movil_7
        X[idx, 7] = desv_movil_7[i]      # desv_movil_7

        y[idx] = serie[i]
        fechas_validas.append(f)

    return X, y, fechas_validas


def validar_sin_fuga(X: np.ndarray, y: np.ndarray, serie_original: np.ndarray) -> bool:
    """
    Verifica que no hay fuga de información del futuro en las features.

    Para cada fila i (que corresponde a día t = WARMUP_DIAS + i en la serie original):
    - lag1 debe ser == serie_original[t-1]
    - lag7 debe ser == serie_original[t-7] (si t>=7)
    - media_movil_7 debe ser == mean(serie_original[t-7:t])
    - desv_movil_7 debe ser == std(serie_original[t-7:t])
    - y debe ser == serie_original[t]

    Retorna True si todo es correcto.
    """
    n = X.shape[0]
    for i in range(n):
        t = WARMUP_DIAS + i

        # lag1
        if t - 1 >= 0:
            if not np.isclose(X[i, 4], serie_original[t - 1]):
                return False

        # lag7
        if t - 7 >= 0:
            if not np.isclose(X[i, 5], serie_original[t - 7]):
                return False

        # media móvil 7
        if t >= 7:
            ventana = serie_original[t - 7:t]
            if not np.isclose(X[i, 6], np.mean(ventana)):
                return False
            if not np.isclose(X[i, 7], np.std(ventana, ddof=0)):
                return False

        # objetivo
        if not np.isclose(y[i], serie_original[t]):
            return False

    return True