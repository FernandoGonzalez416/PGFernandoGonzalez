from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status, Response

from app.core.capacidades import Capacidad
from app.core.db import SesionDB, get_db_session
from app.core.permissions import requiere
from app.core.security import get_usuario_actual_id
from app.schemas.sugerencia import GenerarResultado, SugerenciaRead, SugerenciaUpdate
from app.services import sugerencias as sugerencias_servicio

router = APIRouter()


@router.post(
    "/generar",
    response_model=GenerarResultado,
    status_code=status.HTTP_200_OK,
)
async def generar_sugerencias(
    sesion: Annotated[SesionDB, Depends(get_db_session)],
    _: Annotated[None, Depends(requiere(Capacidad.PREDICCION_VER))],
) -> GenerarResultado:
    return await sugerencias_servicio.generar_sugerencias(sesion)


@router.get(
    "",
    response_model=dict,
)
async def listar_sugerencias(
    sesion: Annotated[SesionDB, Depends(get_db_session)],
    _: Annotated[None, Depends(requiere(Capacidad.SUGERENCIAS_VER))],
    estado: Annotated[
        Literal["pendiente", "atendida", "descartada"] | None,
        Query(description="Filtrar por estado"),
    ] = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 50,
    desplazamiento: Annotated[int, Query(ge=0)] = 0,
):
    return await sugerencias_servicio.listar_sugerencias(
        sesion=sesion,
        estado=estado,
        limite=limite,
        desplazamiento=desplazamiento,
    )


@router.patch(
    "/{sugerencia_id}",
    response_model=SugerenciaRead,
)
async def actualizar_sugerencia(
    sugerencia_id: str,
    payload: SugerenciaUpdate,
    sesion: Annotated[SesionDB, Depends(get_db_session)],
    _: Annotated[None, Depends(requiere(Capacidad.SUGERENCIAS_ATENDER))],
) -> SugerenciaRead:
    sug = await sugerencias_servicio.actualizar_sugerencia(sesion, sugerencia_id, payload)
    return SugerenciaRead.model_validate(sug, from_attributes=True)



