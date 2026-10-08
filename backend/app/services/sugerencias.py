from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.core import config
from app.core.db import SesionDB
from app.core.errores import (
    SugerenciaNoEncontradaError,
    SugerenciaNoPendienteError,
)


def _a_cuantia_2dec(x: Decimal | float) -> Decimal:
    d = x if isinstance(x, Decimal) else Decimal(str(x))
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _ventana_7dias(hoy: date) -> tuple[date, date]:
    inicio = hoy - timedelta(days=6)
    fin = hoy
    return inicio, fin


async def generar_sugerencias(sesion: SesionDB) -> "GenerarResultado":
    from app.schemas.sugerencia import GenerarResultado

    hoy = date.today()
    inicio_v, fin_v = _ventana_7dias(hoy)
    predicciones_creadas = 0
    sugerencias_creadas = 0

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
            ventas_q = await sesion.execute(
                text(
                    "SELECT COALESCE(SUM(dv.cantidad), 0) AS s "
                    "FROM detalle_venta dv "
                    "JOIN venta v ON v.id = dv.venta_id "
                    "WHERE dv.producto_id = :pid AND v.estado = 'activa' "
                    "AND v.fecha >= :ini AND v.fecha <= :fin"
                ),
                {"pid": pid, "ini": inicio_v, "fin": fin_v},
            )
            suma_unidades = Decimal(str(ventas_q.scalar() or 0))
            promedio_diario = (suma_unidades / Decimal("7")) if suma_unidades >= 0 else Decimal("0")
            demanda_pronosticada = _a_cuantia_2dec(promedio_diario * Decimal("7"))

            datos_ficticios_cfg = bool(config.settings.DATOS_FICTICIOS)
            nivel_confianza = "simulacion" if datos_ficticios_cfg else "baja"

            pred_id_q = await sesion.execute(
                text(
                    "INSERT INTO prediccion (producto_id, metodo, nivel_confianza, datos_ficticios, "
                    "inicio_horizonte, fin_horizonte, demanda_pronosticada, observaciones_usadas, intervalo_inf, intervalo_sup) "
                    "VALUES (:pid, 'promedio_movil', :nc, :df, :inih, :finh, :dp, 7, NULL, NULL) RETURNING id"
                ),
                {
                    "pid": pid,
                    "nc": nivel_confianza,
                    "df": datos_ficticios_cfg,
                    "inih": hoy + timedelta(days=1),
                    "finh": hoy + timedelta(days=7),
                    "dp": demanda_pronosticada,
                },
            )
            pred_id = pred_id_q.scalar_one()
            predicciones_creadas += 1

            stock_q = await sesion.execute(
                text("SELECT COALESCE(SUM(cantidad), 0) FROM existencia WHERE producto_id = :pid"),
                {"pid": pid},
            )
            stock_proyectado = _a_cuantia_2dec(stock_q.scalar() or 0)
            umbral_m = _a_cuantia_2dec(p["umbral_minimo"] or 0)
            cantidad_sugerida = demanda_pronosticada - stock_proyectado + umbral_m
            cantidad_sugerida = _a_cuantia_2dec(cantidad_sugerida)
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

    return GenerarResultado(
        predicciones_creadas=predicciones_creadas,
        sugerencias_creadas=sugerencias_creadas,
    )


async def listar_sugerencias(
    sesion: SesionDB,
    estado: str | None = None,
    limite: int = 50,
    desplazamiento: int = 0,
) -> dict[str, Any]:
    base = (
        "SELECT s.id, s.producto_id, s.prediccion_id, s.cantidad_sugerida, "
        "s.prioridad, s.estado, s.stock_proyectado, "
        "s.demanda_pronosticada, s.fecha, p.codigo AS codigo, p.nombre AS nombre "
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
    for f in filas.mappings():
        items.append(dict(f, producto=None))
    total_sql = "SELECT COUNT(*) FROM sugerencia s" + where
    tparams = {"estado": estado} if estado else {}
    total_q = await sesion.execute(text(total_sql), tparams)
    return {"items": items, "total": int(total_q.scalar() or 0)}


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