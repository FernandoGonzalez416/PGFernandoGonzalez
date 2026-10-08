from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.producto import ProductoRef


class SugerenciaRead(BaseModel):
    model_config = {'from_attributes': True}

    id: UUID
    producto_id: UUID
    prediccion_id: UUID
    cantidad_sugerida: Decimal
    prioridad: Literal['baja', 'media', 'alta']
    estado: Literal['pendiente', 'atendida', 'descartada']
    stock_proyectado: Decimal
    demanda_pronosticada: Decimal
    fecha: datetime
    codigo: str | None = None
    nombre: str | None = None
    producto: ProductoRef | None = None


class SugerenciaUpdate(BaseModel):
    model_config = {'extra': 'forbid'}

    estado: Literal['atendida', 'descartada']


class GenerarResultado(BaseModel):
    predicciones_creadas: int = Field(ge=0)
    sugerencias_creadas: int = Field(ge=0)
