from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capacidades import Capacidad
from app.core.db import get_db_session
from app.core.permissions import requiere
from app.schemas.reporte import ProductoMasVendidoItem
from app.services.reportes import obtener_productos_mas_vendidos

router = APIRouter()


@router.get("/productos-mas-vendidos", response_model=list[ProductoMasVendidoItem])
async def productos_mas_vendidos(
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    limite: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db_session),
    _cap = Depends(requiere(Capacidad.REPORTES_VER)),
) -> list[ProductoMasVendidoItem]:
    hoy = date.today()
    if fecha_fin is None:
        f_fin = hoy
    else:
        f_fin = fecha_fin
    if fecha_inicio is None:
        f_ini = hoy - timedelta(days=30)
    else:
        f_ini = fecha_inicio
    if f_fin < f_ini:
        raise HTTPException(status_code=422, detail="fecha_fin no puede ser menor que fecha_inicio")
    datos = await obtener_productos_mas_vendidos(db=db, fecha_inicio=f_ini, fecha_fin=f_fin, limite=limite)
    return [ProductoMasVendidoItem(**d) for d in datos]
