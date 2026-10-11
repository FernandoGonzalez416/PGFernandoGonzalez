from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import text

from app.core import config
from app.core.db import SesionDB
from app.core.errores import (
    SugerenciaNoEncontradaError,
    SugerenciaNoPendienteError,
)
from app.ml import (
    obtener_serie_diaria,
    serie_a_array,
    construir_features,
    evaluar_modelos,
    generar_pronostico_completo,
    determinar_confianza,
    ResultadoEvaluacion,
    NivelConfianza,
)


def _a_cuantia_2dec(x: Decimal | float) -> Decimal:
    d = x if isinstance(x, Decimal) else Decimal(str(x))
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _ventana_7dias(hoy: date) -> tuple[date, date]:
    inicio = hoy - timedelta(days=6)
    fin = hoy
    return inicio, fin


# Thread pool para ejecutar el motor ML sin bloquear el event loop
_executor = ThreadPoolExecutor(max_workers=2)


def _ejecutar_motor_ml_sync(
    serie_data: Dict,
    datos_ficticios: bool,
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline ML completo de forma síncrona.
    Debe correr en thread pool (run_in_threadpool).
    """
    import numpy as np

    unidades = serie_data["unidades"]
    fechas = serie_data["fechas"]
    primera_venta = serie_data["primera_venta"]

    if not unidades or primera_venta is None:
        return {
            "metodo": "promedio_movil",
            "nivel_confianza": "simulacion" if datos_ficticios else "baja",
            "demanda_pronosticada": 0.0,
            "intervalo_inf": None,
            "intervalo_sup": None,
            "mae_validacion": None,
            "wape_validacion": None,
            "nmae": None,
            "mae_linea_base": None,
            "observaciones_usadas": 0,
            "datos_ficticios": datos_ficticios,
            "motivo": "sin historial de ventas",
            "suficiente": False,
        }

    serie = serie_a_array(unidades)
    X, y, fechas_validas = construir_features(serie, fechas)

    if len(X) == 0:
        # Muy pocos datos post-warmup
        return {
            "metodo": "promedio_movil",
            "nivel_confianza": "simulacion" if datos_ficticios else "baja",
            "demanda_pronosticada": float(np.mean(serie[-7:])) * 7 if len(serie) >= 7 else float(np.mean(serie)) * 7,
            "intervalo_inf": None,
            "intervalo_sup": None,
            "mae_validacion": None,
            "wape_validacion": None,
            "nmae": None,
            "mae_linea_base": None,
            "observaciones_usadas": len(serie),
            "datos_ficticios": datos_ficticios,
            "motivo": "insuficientes datos post-warmup",
            "suficiente": False,
        }

    # Evaluar modelos
    resultado_eval: ResultadoEvaluacion = evaluar_modelos(X, y, serie, fechas)

    # Generar pronóstico final
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
        datos_ficticios=datos_ficticios,
    )

    # MAE de línea base
    mae_lb = resultado_eval.metricas_linea_base.mae

    return {
        "metodo": resultado_eval.modelo_seleccionado,
        "nivel_confianza": confianza_result.nivel,
        "demanda_pronosticada": round(demanda_total, 2),
        "intervalo_inf": round(inf, 2) if inf is not None else None,
        "intervalo_sup": round(sup, 2) if sup is not None else None,
        "mae_validacion": round(mae_val, 2) if mae_val is not None else None,
        "wape_validacion": round(wape_val, 2) if wape_val is not None else None,
        "nmae": round(nmae_val, 4) if nmae_val is not None else None,
        "mae_linea_base": round(mae_lb, 2) if mae_lb is not None else None,
        "observaciones_usadas": resultado_eval.observaciones_usadas,
        "datos_ficticios": datos_ficticios,
        "motivo": resultado_eval.motivo_no_suficiente,
        "suficiente": resultado_eval.suficiente,
    }


async def generar_sugerencias(sesion: SesionDB) -> "GenerarResultado":
    from app.schemas.sugerencia import GenerarResultado

    import asyncio

    hoy = date.today()
    predicciones_creadas = 0
    sugerencias_creadas = 0
    por_metodo: Dict[str, int] = {}

    datos_ficticios_cfg = bool(config.settings.DATOS_FICTICIOS)

    async with sesion.begin_nested():
        prods = await sesion.execute(
            text(
                "SELECT id, nombre, codigo, umbral_minimo, activo "
                "FROM producto WHERE activo = true ORDER BY nombre"
            )
        )
        productos = prods.mappings().all()

        for p in productos:
            pid = p["id"]

            # Obtener serie diaria usando el motor ML
            serie_data = await obtener_serie_diaria(sesion, pid)

            # Ejecutar motor ML en thread pool (no bloquea event loop)
            loop = asyncio.get_event_loop()
            ml_result = await loop.run_in_executor(
                _executor,
                _ejecutar_motor_ml_sync,
                serie_data,
                datos_ficticios_cfg,
            )

            # Productos sin ninguna venta: no se pronostican (P3a punto 17)
            if ml_result["motivo"] == "sin historial de ventas":
                # Usar stock mínimo como sugerencia base
                stock_q = await sesion.execute(
                    text("SELECT COALESCE(SUM(cantidad), 0) FROM existencia WHERE producto_id = :pid"),
                    {"pid": pid},
                )
                stock_proyectado = _a_cuantia_2dec(stock_q.scalar() or 0)
                umbral_m = _a_cuantia_2dec(p["umbral_minimo"] or 0)
                cantidad_sugerida = _a_cuantia_2dec(max(0, float(umbral_m) - float(stock_proyectado)))
                demanda_pronosticada = Decimal("0.00")

                # Crear predicción con método "sin_historial"
                pred_id_q = await sesion.execute(
                    text(
                        "INSERT INTO prediccion (producto_id, metodo, nivel_confianza, datos_ficticios, "
                        "inicio_horizonte, fin_horizonte, demanda_pronosticada, observaciones_usadas, "
                        "intervalo_inf, intervalo_sup, mae_linea_base) "
                        "VALUES (:pid, 'sin_historial', :nc, :df, :inih, :finh, :dp, 0, NULL, NULL, NULL) RETURNING id"
                    ),
                    {
                        "pid": pid,
                        "nc": "baja",
                        "df": datos_ficticios_cfg,
                        "inih": hoy + timedelta(days=1),
                        "finh": hoy + timedelta(days=7),
                        "dp": 0,
                    },
                )
                pred_id = pred_id_q.scalar_one()
                predicciones_creadas += 1

            else:
                # Insertar predicción con todos los campos del motor ML
                pred_id_q = await sesion.execute(
                    text(
                        "INSERT INTO prediccion (producto_id, metodo, nivel_confianza, datos_ficticios, "
                        "inicio_horizonte, fin_horizonte, demanda_pronosticada, observaciones_usadas, "
                        "intervalo_inf, intervalo_sup, mae_validacion, wape_validacion, nmae, mae_linea_base) "
                        "VALUES (:pid, :metodo, :nc, :df, :inih, :finh, :dp, :obs, :inf, :sup, :mae, :wape, :nmae, :mae_lb) RETURNING id"
                    ),
                    {
                        "pid": pid,
                        "metodo": ml_result["metodo"],
                        "nc": ml_result["nivel_confianza"],
                        "df": datos_ficticios_cfg,
                        "inih": hoy + timedelta(days=1),
                        "finh": hoy + timedelta(days=7),
                        "dp": _a_cuantia_2dec(ml_result["demanda_pronosticada"]),
                        "obs": ml_result["observaciones_usadas"],
                        "inf": _a_cuantia_2dec(ml_result["intervalo_inf"]) if ml_result["intervalo_inf"] is not None else None,
                        "sup": _a_cuantia_2dec(ml_result["intervalo_sup"]) if ml_result["intervalo_sup"] is not None else None,
                        "mae": _a_cuantia_2dec(ml_result["mae_validacion"]) if ml_result["mae_validacion"] is not None else None,
                        "wape": _a_cuantia_2dec(ml_result["wape_validacion"]) if ml_result["wape_validacion"] is not None else None,
                        "nmae": _a_cuantia_2dec(ml_result["nmae"]) if ml_result["nmae"] is not None else None,
                        "mae_lb": _a_cuantia_2dec(ml_result["mae_linea_base"]) if ml_result["mae_linea_base"] is not None else None,
                    },
                )
                pred_id = pred_id_q.scalar_one()
                predicciones_creadas += 1

                # Contar por método
                metodo = ml_result["metodo"]
                por_metodo[metodo] = por_metodo.get(metodo, 0) + 1

                # Usar la demanda pronosticada del motor ML
                demanda_pronosticada = _a_cuantia_2dec(ml_result["demanda_pronosticada"])

            # Calcular sugerencia (igual para ambos casos)
            stock_q = await sesion.execute(
                text("SELECT COALESCE(SUM(cantidad), 0) FROM existencia WHERE producto_id = :pid"),
                {"pid": pid},
            )
            stock_proyectado = _a_cuantia_2dec(stock_q.scalar() or 0)
            umbral_m = _a_cuantia_2dec(p["umbral_minimo"] or 0)

            if ml_result["motivo"] == "sin historial de ventas":
                cantidad_sugerida = _a_cuantia_2dec(max(0, float(umbral_m) - float(stock_proyectado)))
            else:
                cantidad_sugerida = _a_cuantia_2dec(demanda_pronosticada - stock_proyectado + umbral_m)
                if cantidad_sugerida < Decimal("0.00"):
                    cantidad_sugerida = Decimal("0.00")

            ya_pend = await sesion.execute(
                text("SELECT id FROM sugerencia WHERE producto_id = :pid AND estado = 'pendiente' LIMIT 1"),
                {"pid": pid},
            )
            if cantidad_sugerida > Decimal("0.00") and ya_pend.scalar_one_or_none() is None:
                if stock_proyectado <= umbral_m:
                    prioridad = "alta"
                elif stock_proyectado < demanda_pronosticada:
                    prioridad = "media"
                else:
                    prioridad = "baja"
                await sesion.execute(
                    text(
                        "INSERT INTO sugerencia (producto_id, prediccion_id, cantidad_sugerida, prioridad, estado, stock_proyectado, demanda_pronosticada) "
                        "VALUES (:pid, :predid, :cant, :prio, 'pendiente', :sp, :dp)"
                    ),
                    {
                        "pid": pid,
                        "predid": pred_id,
                        "cant": cantidad_sugerida,
                        "prio": prioridad,
                        "sp": stock_proyectado,
                        "dp": demanda_pronosticada,
                    },
                )
                sugerencias_creadas += 1

        if sugerencias_creadas > 0:
            await sesion.execute(
                text(
                    "INSERT INTO notificacion (tipo, mensaje, usuario_id, leida) "
                    "VALUES ('sugerencia_compra', :msg, NULL, false)"
                ),
                {"msg": f"Se generaron {sugerencias_creadas} sugerencia(s) de reabastecimiento pendientes de revisar."},
            )

    # Agregar por_metodo al resultado
    resultado = GenerarResultado(
        predicciones_creadas=predicciones_creadas,
        sugerencias_creadas=sugerencias_creadas,
    )
    # Agregar campo dinámicamente (el schema lo permite con extra)
    resultado.__dict__["por_metodo"] = por_metodo
    return resultado


async def listar_sugerencias(
    sesion: SesionDB,
    estado: str | None = None,
    limite: int = 50,
    desplazamiento: int = 0,
) -> dict[str, Any]:
    base = (
        "SELECT s.id, s.producto_id, s.prediccion_id, s.cantidad_sugerida, "
        "s.prioridad, s.estado, s.stock_proyectado, "
        "s.demanda_pronosticada, s.fecha, p.codigo AS codigo, p.nombre AS nombre, "
        "COUNT(*) OVER() AS total "
        "FROM sugerencia s LEFT JOIN producto p ON p.id = s.producto_id"
    )
    params: dict[str, Any] = {"lim": limite, "off": desplazamiento}
    where = ""
    if estado:
        where = " WHERE s.estado = :estado"
        params["estado"] = estado
    sql = f"{base}{where} ORDER BY s.fecha DESC OFFSET :off LIMIT :lim"
    filas = await sesion.execute(text(sql), params)
    items: list[dict[str, Any]] = []
    total = 0
    for f in filas.mappings():
        fila = dict(f)
        total = int(fila.pop("total") or 0)
        items.append(dict(fila, producto=None))
    return {"items": items, "total": total}


async def actualizar_sugerencia(
    sesion: SesionDB, sugerencia_id: str, payload: "SugerenciaUpdate"
) -> Any:
    from app.schemas.sugerencia import SugerenciaUpdate

    try:
        sug_id = UUID(str(sugerencia_id))
    except Exception:
        raise SugerenciaNoEncontradaError

    r = await sesion.execute(text("SELECT id, estado FROM sugerencia WHERE id = :sid"), {"sid": sug_id})
    row = r.mappings().first()
    if not row:
        raise SugerenciaNoEncontradaError
    if row["estado"] != "pendiente":
        raise SugerenciaNoPendienteError
    await sesion.execute(
        text("UPDATE sugerencia SET estado = :est WHERE id = :sid"),
        {"est": payload.estado, "sid": sug_id},
    )
    fres = await sesion.execute(text("SELECT * FROM sugerencia WHERE id = :sid"), {"sid": sug_id})
    return fres.mappings().first()