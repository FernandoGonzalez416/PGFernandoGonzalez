from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class NotificacionRead(BaseModel):
    model_config = {'from_attributes': True}

    id: UUID
    tipo: Literal['bajo_stock', 'vencimiento_proximo', 'sugerencia_compra', 'sistema']
    mensaje: str
    usuario_id: UUID | None = None
    leida: bool = False
    fecha: datetime

