"""Candidatos de modelos para predicción de demanda."""

from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer


RANDOM_STATE = 42


def crear_modelos() -> dict:
    """
    Crea el diccionario de candidatos de modelos.

    Returns:
        dict con claves 'random_forest', 'hist_gradient_boosting', 'ridge'
        y valores Pipeline de sklearn listos para fit/predict.
    """
    # Column indices in feature matrix:
    # 0: dow, 1: mes, 2: fin_semana, 3: tendencia
    # 4: lag1, 5: lag7, 6: media_movil_7, 7: desv_movil_7

    # Random Forest: sin escalado, maneja variables categóricas nativamente
    rf = Pipeline([
        ("model", RandomForestRegressor(
            n_estimators=200,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )),
    ])

    # HistGradientBoosting: maneja NaN nativamente, pérdida de media (M1-TER:
    # la mediana colapsaba a cero en demanda intermitente)
    hgb = Pipeline([
        ("model", HistGradientBoostingRegressor(
            random_state=RANDOM_STATE,
        )),
    ])

    # Ridge: requiere one-hot en dow/mes y escalado en numéricas
    preprocess = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), [0, 1]),
            ("num", StandardScaler(), [2, 3, 4, 5, 6, 7]),
        ],
        remainder="passthrough",
    )
    ridge = Pipeline([
        ("preprocess", preprocess),
        ("model", Ridge(random_state=RANDOM_STATE)),
    ])

    return {
        "random_forest": rf,
        "hist_gradient_boosting": hgb,
        "ridge": ridge,
    }


def nombre_metodo_clave_a_bd(clave: str) -> str:
    """Convierte clave interna a valor para BD (según CHECK constraint)."""
    mapa = {
        "random_forest": "random_forest",
        "hist_gradient_boosting": "hist_gradient_boosting",
        "ridge": "ridge",
        "promedio_movil": "promedio_movil",
    }
    return mapa.get(clave, clave)