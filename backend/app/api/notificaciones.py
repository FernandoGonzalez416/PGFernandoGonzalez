from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, Response

from app.core.capacidades import Capacidad
from app.core.db import SesionDB, get_db_session
from app.core.permissions import requiere
from app.core.security import get_usuario_actual_id
from app.schemas.notificacion import NotificacionRead
from app.services import notificaciones as notificaciones_servicio

router = APIRouter()


@router.get(
    "",
    response_model=dict,
)
async def listar_notificaciones(
    sesion: Annotated[SesionDB, Depends(get_db_session)],
    _: Annotated[None, Depends(requiere(Capacidad.ALERTAS_VER))],
    usuario_id: Annotated[str | None, Depends(get_usuario_actual_id)] = None,
    leida: Annotated[bool | None, Query(description="Filtrar por leida")] = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 50,
    desplazamiento: Annotated[int, Query(ge=0)] = 0,
):
    return await notificaciones_servicio.listar_notificaciones(
        sesion=sesion,
        usuario_id=usuario_id,
        leida=leida,
        limite=limite,
        desplazamiento=desplazamiento,
    )


@router.patch(
    "/{notificacion_id}/leida",
    status_code=status.HTTP_200_OK,
)
async def marcar_notificacion_leida(
    notificacion_id: str,
    sesion: Annotated[SesionDB, Depends(get_db_session)],
    usuario_id: Annotated[str | None, Depends(get_usuario_actual_id)],
    _: Annotated[None, Depends(requiere(Capacidad.ALERTAS_VER))],
) -> dict:
    await notificaciones_servicio.marcar_notificacion_leida(
        sesion, notificacion_id, usuario_id
    )
    return {"ok": True}



