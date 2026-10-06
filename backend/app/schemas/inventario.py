from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class MovimientoRead(BaseModel):
    """Fila de `movimiento_inventario` tal cual se almacena.

    Bitácora inmutable de la tesis: `cantidad` es siempre una magnitud
    positiva y la dirección del cambio vive en `tipo`.
    """

    id: UUID
    producto_id: UUID
    almacen_id: UUID | None
    tipo: str
    referencia_tipo: str
    referencia_id: UUID | None
    cantidad: Decimal
    usuario_id: UUID | None
    nota: str | None
    fecha: datetime
