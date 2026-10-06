from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capacidades import Capacidad
from app.core.db import get_db_session
from app.core.permissions import requiere
from app.core.security import UsuarioAutenticado
from app.schemas.existencia import ExistenciaAjuste, ExistenciaRead
from app.schemas.inventario import MovimientoRead
from app.services import existencia as servicio

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/existencia", response_model=list[ExistenciaRead])
async def listar_existencias(
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.STOCK_CONSULTAR))],
    producto_id: UUID | None = None,
) -> list[ExistenciaRead]:
    return await servicio.listar_existencias(sesion, producto_id=producto_id)


@router.get("/movimientos", response_model=list[MovimientoRead])
async def listar_movimientos(
    sesion: Session,
    _: Annotated[
        UsuarioAutenticado, Depends(requiere(Capacidad.INVENTARIO_VER_MOVIMIENTOS))
    ],
    producto_id: UUID | None = None,
    limite: int = Query(default=50, ge=1, le=100),
    desplazamiento: int = Query(default=0, ge=0),
) -> list[MovimientoRead]:
    return await servicio.listar_movimientos(
        sesion,
        producto_id=producto_id,
        limite=limite,
        desplazamiento=desplazamiento,
    )


@router.post("/ajustes", response_model=ExistenciaRead, status_code=201)
async def ajustar(
    datos: ExistenciaAjuste,
    sesion: Session,
    usuario: Annotated[
        UsuarioAutenticado, Depends(requiere(Capacidad.INVENTARIO_AJUSTAR))
    ],
) -> ExistenciaRead:
    return await servicio.ajustar_existencia(sesion, datos, usuario.id)
