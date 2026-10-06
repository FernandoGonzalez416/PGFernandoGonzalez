from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.dinero import a_cuantia


class ProductoCreate(BaseModel):
    codigo: str = Field(min_length=1, max_length=50)
    nombre: str = Field(min_length=1, max_length=150)
    descripcion: str | None = None
    categoria_id: UUID
    proveedor_id: UUID | None = None
    precio_venta: Decimal = Field(ge=0, max_digits=12)
    precio_costo: Decimal = Field(ge=0, max_digits=12)
    unidad_medida: str = Field(default="unidad", min_length=1, max_length=30)
    umbral_minimo: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12)
    dias_vencimiento_aviso: int = Field(default=30, ge=0)
    fecha_vencimiento: date | None = None
    fecha_ingreso: date | None = None
    cantidad_inicial: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12)

    def cuantizado(self) -> "ProductoCreate":
        return self.model_copy(
            update={
                "precio_venta": a_cuantia(self.precio_venta),
                "precio_costo": a_cuantia(self.precio_costo),
                "umbral_minimo": a_cuantia(self.umbral_minimo),
                "cantidad_inicial": a_cuantia(self.cantidad_inicial),
            }
        )


class ProductoUpdate(BaseModel):
    # `extra="forbid"`: un campo no declarado se rechaza con 422 en vez de
    # ignorarse en silencio. Es lo que hace que `codigo` (inmutable) y `id`
    # devuelvan error explícito en un PATCH, en lugar de un 200 engañoso.
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = None
    categoria_id: UUID | None = None
    proveedor_id: UUID | None = None
    precio_venta: Decimal | None = Field(default=None, ge=0, max_digits=12)
    precio_costo: Decimal | None = Field(default=None, ge=0, max_digits=12)
    unidad_medida: str | None = Field(default=None, min_length=1, max_length=30)
    umbral_minimo: Decimal | None = Field(default=None, ge=0, max_digits=12)
    dias_vencimiento_aviso: int | None = Field(default=None, ge=0)
    fecha_vencimiento: date | None = None
    fecha_ingreso: date | None = None
    activo: bool | None = None


class ProductoRead(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    descripcion: str | None
    categoria_id: UUID
    proveedor_id: UUID | None
    precio_venta: Decimal
    precio_costo: Decimal
    unidad_medida: str
    umbral_minimo: Decimal
    dias_vencimiento_aviso: int
    fecha_vencimiento: date | None
    fecha_ingreso: date | None
    activo: bool
    created_at: datetime
    updated_at: datetime
    existencia: Decimal