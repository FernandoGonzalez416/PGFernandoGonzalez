from typing import Annotated
from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capacidades import Capacidad
from app.core.db import get_db_session
from app.core.permissions import requiere
from app.core.security import UsuarioAutenticado
from app.schemas.venta import (
    AnulacionCreate,
    ResumenVentas,
    VentaCreate,
    VentaRead,
)
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


@router.get("/resumen", response_model=ResumenVentas)
async def resumen_de_ventas(
    sesion: Session,
    _: Annotated[UsuarioAutenticado, Depends(requiere(Capacidad.STOCK_CONSULTAR))],
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
) -> ResumenVentas:
    hoy = date.today()
    f_fin = fecha_fin if fecha_fin is not None else hoy
    f_ini = fecha_inicio if fecha_inicio is not None else hoy - timedelta(days=6)
    if f_fin < f_ini:
        raise HTTPException(
            status_code=422,
            detail="fecha_fin no puede ser menor que fecha_inicio",
        )
    return await servicio.resumen_ventas(sesion, f_ini, f_fin)


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
    respuesta: Response,
) -> VentaRead:
    """Registra la venta. Una repetición idempotente responde 200, no 201 (P27/F5)."""
    resultado = await servicio.registrar_venta(sesion, datos, usuario.id)
    if not resultado.creada:
        respuesta.status_code = 200
    return resultado.venta


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