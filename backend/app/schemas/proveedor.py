from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.dinero import a_cuantia


class ProveedorCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    contacto: str | None = None
    telefono: str | None = None
    email: str | None = None
    condiciones_entrega: str | None = None
    precio_habitual: Decimal | None = Field(default=None, ge=0, max_digits=12)

    def cuantizado(self) -> "ProveedorCreate":
        if self.precio_habitual is None:
            return self
        return self.model_copy(update={"precio_habitual": a_cuantia(self.precio_habitual)})


class ProveedorUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    contacto: str | None = None
    telefono: str | None = None
    email: str | None = None
    condiciones_entrega: str | None = None
    precio_habitual: Decimal | None = Field(default=None, ge=0, max_digits=12)
    activo: bool | None = None


class ProveedorRead(BaseModel):
    id: UUID
    nombre: str
    contacto: str | None
    telefono: str | None
    email: str | None
    condiciones_entrega: str | None
    precio_habitual: Decimal | None
    activo: bool
    created_at: datetime
    updated_at: datetime