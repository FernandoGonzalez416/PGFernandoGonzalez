from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capacidades import Capacidad
from app.core.db import get_db_session
from app.core.permissions import requiere
from app.core.security import UsuarioAutenticado
from app.schemas.categoria import CategoriaCreate, CategoriaRead, CategoriaUpdate
from app.services import categorias as servicio

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=list[CategoriaRead])
async def listar(
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.PRODUCTOS_CONSULTAR))],
    incluir_inactivas: bool = False,
) -> list[CategoriaRead]:
    return await servicio.listar_categorias(sesion, incluir_inactivas)


@router.post("", response_model=CategoriaRead, status_code=201)
async def crear(
    datos: CategoriaCreate,
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.CATEGORIAS_GESTIONAR))],
) -> CategoriaRead:
    return await servicio.crear_categoria(sesion, datos)


@router.patch("/{categoria_id}", response_model=CategoriaRead)
async def actualizar(
    categoria_id: UUID,
    datos: CategoriaUpdate,
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.CATEGORIAS_GESTIONAR))],
) -> CategoriaRead:
    return await servicio.actualizar_categoria(sesion, categoria_id, datos)