from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.capacidades import Capacidad
from app.core.db import SesionDB, get_db_session
from app.core.permissions import requiere
from app.ml import obtener_serie_diaria, serie_a_array, construir_features, evaluar_modelos, generar_pronostico_completo, determinar_confianza

router = APIRouter(prefix="/predicciones", tags=["predicciones"])


class PrediccionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    producto_id: UUID
    codigo: str
    nombre: str
    metodo: str
    nivel_confianza: Literal["alta", "baja", "simulacion"]
    demanda_pronosticada: float
    intervalo_inf: float | None
    intervalo_sup: float | None
    mae_validacion: float | None
    mae_linea_base: float | None
    mejora_pct: float | None
    observaciones_usadas: int
    fecha_generacion: str


class SerieResponse(BaseModel):
    historial: list[dict]
    pronostico: list[dict]
    metodo: str
    mae_modelo: float | None
    mae_linea_base: float | None
    nivel_confianza: str
    suficiente: bool
    motivo: str | None


@router.get(
    "",
    response_model=list[PrediccionRead],
)
async def listar_predicciones(
    sesion: Annotated[SesionDB, Depends(get_db_session)],
    _: Annotated[None, Depends(requiere(Capacidad.PREDICCION_VER))],
):
    """Última predicción por producto activo (solo admin - Capacidad.PREDICCION_VER)."""
    from sqlalchemy import text

    filas = await sesion.execute(
        text(
            """
            SELECT DISTINCT ON (p.id)
                pr.id, pr.producto_id, pr.metodo, pr.nivel_confianza,
                pr.demanda_pronosticada, pr.intervalo_inf, pr.intervalo_sup,
                pr.mae_validacion, pr.mae_linea_base, pr.observaciones_usadas,
                pr.fecha_generacion, p.codigo, p.nombre
            FROM prediccion pr
            JOIN producto p ON p.id = pr.producto_id
            WHERE p.activo = true
            ORDER BY p.id, pr.fecha_generacion DESC
            """
        )
    )

    resultado = []
    for f in filas.mappings():
        mae_val = f["mae_validacion"]
        mae_lb = f["mae_linea_base"]
        mejora = None
        if mae_lb is not None and mae_val is not None and mae_lb > 0:
            mejora = round((float(mae_lb) - float(mae_val)) / float(mae_lb) * 100, 1)

        resultado.append(
            PrediccionRead(
                id=f["id"],
                producto_id=f["producto_id"],
                codigo=f["codigo"],
                nombre=f["nombre"],
                metodo=f["metodo"],
                nivel_confianza=f["nivel_confianza"],
                demanda_pronosticada=float(f["demanda_pronosticada"] or 0),
                intervalo_inf=float(f["intervalo_inf"]) if f["intervalo_inf"] is not None else None,
                intervalo_sup=float(f["intervalo_sup"]) if f["intervalo_sup"] is not None else None,
                mae_validacion=float(mae_val) if mae_val is not None else None,
                mae_linea_base=float(mae_lb) if mae_lb is not None else None,
                mejora_pct=mejora,
                observaciones_usadas=f["observaciones_usadas"] or 0,
                fecha_generacion=f["fecha_generacion"].isoformat() if f["fecha_generacion"] else "",
            )
        )
    return resultado


@router.get(
    "/{producto_id}/serie",
    response_model=SerieResponse,
)
async def obtener_serie_prediccion(
    producto_id: UUID,
    sesion: Annotated[SesionDB, Depends(get_db_session)],
    _: Annotated[None, Depends(requiere(Capacidad.PREDICCION_VER))],
):
    """
    Recalcula la serie y pronóstico SIN persistir.
    Devuelve historial (últimos 60 días), pronóstico (7 días), métricas y diagnóstico.
    """
    from app.ml import ResultadoEvaluacion
    import numpy as np

    # Verificar que el producto existe
    from sqlalchemy import text
    prod = await sesion.execute(
        text("SELECT id, codigo, nombre FROM producto WHERE id = :pid"),
        {"pid": producto_id},
    )
    prod_row = prod.mappings().first()
    if not prod_row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Obtener serie diaria
    serie_data = await obtener_serie_diaria(sesion, producto_id)
    unidades = serie_data["unidades"]
    fechas = serie_data["fechas"]
    primera_venta = serie_data["primera_venta"]

    if not unidades or primera_venta is None:
        return SerieResponse(
            historial=[],
            pronostico=[],
            metodo="sin_historial",
            mae_modelo=None,
            mae_linea_base=None,
            nivel_confianza="baja",
            suficiente=False,
            motivo="Producto sin ventas registradas",
        )

    serie = serie_a_array(unidades)
    X, y, fechas_validas = construir_features(serie, fechas)

    if len(X) == 0:
        # Muy pocos datos
        ultimos_60 = list(zip([f.isoformat() for f in fechas[-60:]], unidades[-60:]))
        return SerieResponse(
            historial=[{"fecha": f, "unidades": u} for f, u in ultimos_60],
            pronostico=[],
            metodo="promedio_movil",
            mae_modelo=None,
            mae_linea_base=None,
            nivel_confianza="baja",
            suficiente=False,
            motivo="Insuficientes datos post-warmup (14 días)",
        )

    # Evaluar (sin persistir)
    resultado_eval: ResultadoEvaluacion = evaluar_modelos(X, y, serie, fechas)

    # Generar pronóstico
    pronostico_7dias, demanda_total, inf, sup, mae_val, wape_val = generar_pronostico_completo(
        resultado_eval, X, y, serie
    )

    # Determinar confianza
    modelo_vence = resultado_eval.modelo_seleccionado != "promedio_movil"
    nmae_val = resultado_eval.metricas_modelo.nmae
    confianza_result = determinar_confianza(
        suficiente=resultado_eval.suficiente,
        modelo_vence_linea_base=modelo_vence,
        nmae=nmae_val,
        datos_ficticios=False,  # Para la vista de serie, asumimos datos reales
    )

    # Historial últimos 60 días
    ultimos_60 = list(zip([f.isoformat() for f in fechas[-60:]], unidades[-60:]))

    # Pronóstico 7 días con fechas futuras
    from datetime import date, timedelta
    hoy = date.today()
    pronostico_fechas = [(hoy + timedelta(days=i+1)).isoformat() for i in range(7)]
    pronostico_lista = [
        {"fecha": f, "unidades": round(float(u), 2)}
        for f, u in zip(pronostico_fechas, pronostico_7dias)
    ]

    mae_lb = resultado_eval.metricas_linea_base.mae

    return SerieResponse(
        historial=[{"fecha": f, "unidades": u} for f, u in ultimos_60],
        pronostico=pronostico_lista,
        metodo=resultado_eval.modelo_seleccionado,
        mae_modelo=round(mae_val, 2) if mae_val is not None else None,
        mae_linea_base=round(mae_lb, 2) if mae_lb is not None else None,
        nivel_confianza=confianza_result.nivel,
        suficiente=resultado_eval.suficiente,
        motivo=resultado_eval.motivo_no_suficiente,
    )