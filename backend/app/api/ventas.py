from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capacidades import Capacidad
from app.core.db import get_db_session
from app.core.permissions import requiere
from app.core.security import UsuarioAutenticado
from app.schemas.venta import AnulacionCreate, VentaCreate, VentaRead
from app.services import ventas as servicio

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=list[VentaRead])
async def listar_ventas(
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.STOCK_CONSULTAR))],
    limite: int = Query(default=50, ge=1, le=100),
    desplazamiento: int = Query(default=0, ge=0),
) -> list[VentaRead]:
    return await servicio.listar_ventas(
        sesion, limite=limite, desplazamiento=desplazamiento
    )


@router.get("/{venta_id}", response_model=VentaRead)
async def obtener_venta(
    venta_id: UUID,
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.STOCK_CONSULTAR))],
) -> VentaRead:
    return await servicio.obtener_venta(sesion, venta_id)


@router.post("", response_model=VentaRead, status_code=201)
async def registrar_venta(
    datos: VentaCreate,
    sesion: Session,
    usuario: Annotated[
        UsuarioAutenticado, Depends(requiere(Capacidad.VENTAS_REGISTRAR))
    ],
) -> VentaRead:
    return await servicio.registrar_venta(sesion, datos, usuario.id)


@router.post("/{venta_id}/anular", response_model=VentaRead)
async def anular_venta(
    venta_id: UUID,
    datos: AnulacionCreate,
    sesion: Session,
    usuario: Annotated[
        UsuarioAutenticado, Depends(requiere(Capacidad.VENTAS_ANULAR))
    ],
) -> VentaRead:
    return await servicio.anular_venta(sesion, venta_id, usuario.id, usuario.rol, datos)