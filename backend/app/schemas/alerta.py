from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class AlertaStockBajo(BaseModel):
    producto_id: UUID
    codigo: str
    nombre: str
    existencia: Decimal
    umbral_minimo: Decimal
    almacen_id: UUID | None = None
    agotado: bool


class AlertaVencimientoProximo(BaseModel):
    producto_id: UUID
    codigo: str
    nombre: str
    fecha_vencimiento: date | None
    dias_vencimiento_aviso: int
    dias_restantes: int | None
    almacen_id: UUID | None = None
    vencido: bool


class AlertaResumen(BaseModel):
    bajo_stock: list[AlertaStockBajo]
    vencimiento_proximo: list[AlertaVencimientoProximo]

