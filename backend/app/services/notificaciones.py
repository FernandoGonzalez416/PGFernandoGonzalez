from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SesionDB
from app.core.errores import NotificacionNoEncontradaError


async def listar_notificaciones(
    sesion: SesionDB,
    usuario_id: str | None = None,
    leida: bool | None = None,
    limite: int = 50,
    desplazamiento: int = 0,
) -> dict[str, Any]:
    params: dict[str, Any] = {"lim": limite, "off": desplazamiento}
    where = []
    if usuario_id:
        try:
            uid = UUID(str(usuario_id))
            where.append("(usuario_id = :uid OR usuario_id IS NULL)")
            params["uid"] = uid
        except Exception:
            where.append("(usuario_id IS NULL)")
    if leida is not None:
        where.append("leida = :leida")
        params["leida"] = leida
    sql = "SELECT id, tipo, mensaje, usuario_id, leida, fecha FROM notificacion"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY fecha DESC OFFSET :off LIMIT :lim"
    filas = await sesion.execute(text(sql), params)
    items = [dict(f) for f in filas.mappings()]
    total_where = " WHERE " + " AND ".join(where) if where else ""
    total_q = await sesion.execute(text("SELECT COUNT(*) FROM notificacion" + total_where), {k: v for k, v in params.items() if k != "lim" and k != "off"})
    return {"items": items, "total": int(total_q.scalar() or 0)}


async def marcar_notificacion_leida(
    sesion: SesionDB, notificacion_id: str, usuario_id: str | None
) -> None:
    try:
        nid = UUID(str(notificacion_id))
    except Exception:
        raise NotificacionNoEncontradaError
    r = await sesion.execute(text("SELECT id, usuario_id FROM notificacion WHERE id = :nid"), {"nid": nid})
    n = r.mappings().first()
    if not n:
        raise NotificacionNoEncontradaError
    if n["usuario_id"] is not None and usuario_id:
        try:
            uid = UUID(str(usuario_id))
        except Exception:
            uid = None
        if n["usuario_id"] != uid:
            raise NotificacionNoEncontradaError
    await sesion.execute(text("UPDATE notificacion SET leida = true WHERE id = :nid"), {"nid": nid})
    await sesion.flush()

