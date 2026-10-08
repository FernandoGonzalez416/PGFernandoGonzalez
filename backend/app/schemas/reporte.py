from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ProductoMasVendidoItem(BaseModel):
    producto_id: UUID
    codigo: str
    nombre: str
    cantidad_vendida: Decimal
    total_vendido: Decimal | None = None

