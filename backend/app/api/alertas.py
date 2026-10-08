from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capacidades import Capacidad
from app.core.db import get_db_session
from app.core.permissions import requiere
from app.schemas.alerta import AlertaResumen
from app.services.alertas import obtener_resumen_alertas

router = APIRouter()


@router.get("/", response_model=AlertaResumen)
async def listar_alertas(
    db: AsyncSession = Depends(get_db_session),
    _cap = Depends(requiere(Capacidad.ALERTAS_VER)),
) -> AlertaResumen:
    resumen = await obtener_resumen_alertas(db)
    return AlertaResumen(**resumen)
