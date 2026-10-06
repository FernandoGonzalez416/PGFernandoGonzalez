from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capacidades import Capacidad
from app.core.db import get_db_session
from app.core.permissions import requiere
from app.core.security import UsuarioAutenticado
from app.schemas.existencia import ExistenciaRead
from app.schemas.producto import ProductoCreate, ProductoRead, ProductoUpdate
from app.services import productos as servicio

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=list[ProductoRead])
async def listar(
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.PRODUCTOS_CONSULTAR))],
    q: str | None = Query(default=None, max_length=150),
    categoria_id: UUID | None = None,
    incluir_inactivos: bool = False,
    limite: int = Query(default=50, ge=1, le=100),
    desplazamiento: int = Query(default=0, ge=0),
) -> list[ProductoRead]:
    return await servicio.listar_productos(
        sesion,
        q=q,
        categoria_id=categoria_id,
        incluir_inactivos=incluir_inactivos,
        limite=limite,
        desplazamiento=desplazamiento,
    )


@router.post("", response_model=ProductoRead, status_code=201)
async def crear(
    datos: ProductoCreate,
    sesion: Session,
    usuario: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.PRODUCTOS_EDITAR))],
) -> ProductoRead:
    return await servicio.crear_producto(sesion, datos, usuario.id)


@router.get("/{producto_id}", response_model=ProductoRead)
async def obtener(
    producto_id: UUID,
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.PRODUCTOS_CONSULTAR))],
) -> ProductoRead:
    return await servicio.obtener_producto(sesion, producto_id)


@router.patch("/{producto_id}", response_model=ProductoRead)
async def actualizar(
    producto_id: UUID,
    datos: ProductoUpdate,
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.PRODUCTOS_EDITAR))],
) -> ProductoRead:
    return await servicio.actualizar_producto(sesion, producto_id, datos)


@router.get("/{producto_id}/existencia", response_model=list[ExistenciaRead])
async def listar_existencias(
    producto_id: UUID,
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.STOCK_CONSULTAR))],
) -> list[ExistenciaRead]:
    return await servicio.listar_existencias(sesion, producto_id)