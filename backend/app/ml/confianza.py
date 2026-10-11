"""Cálculo del nivel de confianza (P13)."""

from dataclasses import dataclass
from typing import Literal


NivelConfianza = Literal["alta", "baja", "simulacion"]


@dataclass(frozen=True)
class ResultadoConfianza:
    nivel: NivelConfianza
    razones: list[str]


def determinar_confianza(
    *,
    suficiente: bool,
    modelo_vence_linea_base: bool,
    nmae: float,
    datos_ficticios: bool,
) -> ResultadoConfianza:
    """
    Determina el nivel de confianza según P13.

    Reglas:
    - 'simulacion': si DATOS_FICTICIOS=true (datos de desarrollo)
    - 'alta': solo si TODAS se cumplen:
        1. Suficiencia (ventana >= 75 días Y densidad >= 20/3)
        2. Modelo vence a línea base en validación
        3. nMAE < 1.0 (error medio <= demanda media diaria)
        4. Datos NO son ficticios (entrenado con datos reales del piloto)
    - 'baja': cualquier otro caso
    """
    if datos_ficticios:
        return ResultadoConfianza(
            nivel="simulacion",
            razones=["datos de desarrollo (DATOS_FICTICIOS=true)"],
        )

    if not suficiente:
        return ResultadoConfianza(
            nivel="baja",
            razones=["historial insuficiente (no cumple criterio P13)"],
        )

    if not modelo_vence_linea_base:
        return ResultadoConfianza(
            nivel="baja",
            razones=["el modelo no supera a la línea base (promedio móvil 7 días)"],
        )

    if nmae >= 1.0:
        return ResultadoConfianza(
            nivel="baja",
            razones=[f"nMAE ({nmae:.2f}) >= 1.0: error medio >= demanda media diaria"],
        )

    return ResultadoConfianza(
        nivel="alta",
        razones=[
            "cumple suficiencia (P13)",
            "vence a línea base",
            f"nMAE ({nmae:.2f}) < 1.0",
            "datos reales del piloto",
        ],
    )


# Tabla de casos de prueba (para tests)
CASOS_PRUEBA_CONFIANZA = [
    # (suficiente, vence_base, nmae, datos_ficticios, esperado, descripcion)
    (True, True, 0.5, False, "alta", "caso ideal: todo OK con datos reales"),
    (True, True, 0.8, False, "alta", "nMAE < 1.0"),
    (True, True, 1.0, False, "baja", "nMAE == 1.0 -> baja"),
    (True, True, 1.2, False, "baja", "nMAE > 1.0 -> baja"),
    (True, False, 0.5, False, "baja", "no vence a línea base"),
    (False, True, 0.5, False, "baja", "insuficiente"),
    (True, True, 0.5, True, "simulacion", "datos ficticios -> simulación"),
    (False, False, 0.5, True, "simulacion", "datos ficticios -> simulación (prevalece)"),
    (False, True, 1.5, True, "simulacion", "datos ficticios -> simulación (prevalece)"),
]