from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capacidades import Capacidad
from app.core.db import get_db_session
from app.core.permissions import requiere
from app.core.security import UsuarioAutenticado
from app.schemas.proveedor import ProveedorCreate, ProveedorRead, ProveedorUpdate
from app.services import proveedores as servicio

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=list[ProveedorRead])
async def listar(
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.STOCK_CONSULTAR))],
    incluir_inactivos: bool = False,
) -> list[ProveedorRead]:
    return await servicio.listar_proveedores(sesion, incluir_inactivos)


@router.post("", response_model=ProveedorRead, status_code=201)
async def crear(
    datos: ProveedorCreate,
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.PROVEEDORES_GESTIONAR))],
) -> ProveedorRead:
    return await servicio.crear_proveedor(sesion, datos)


@router.patch("/{proveedor_id}", response_model=ProveedorRead)
async def actualizar(
    proveedor_id: UUID,
    datos: ProveedorUpdate,
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.PROVEEDORES_GESTIONAR))],
) -> ProveedorRead:
    return await servicio.actualizar_proveedor(sesion, proveedor_id, datos)