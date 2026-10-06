from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ExistenciaRead(BaseModel):
    producto_id: UUID
    almacen_id: UUID
    almacen_nombre: str
    cantidad: Decimal
    updated_at: datetime