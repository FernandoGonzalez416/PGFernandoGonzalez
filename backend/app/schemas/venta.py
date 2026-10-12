from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.dinero import a_cuantia


class VentaDetalleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    producto_id: UUID
    cantidad: int = Field(ge=1)


class VentaCreate(BaseModel):
    """Contrato de `POST /api/ventas` (acordado en P25-b).

    El precio no viaja en el request: lo lee el backend de
    `producto.precio_venta` dentro de la transacción (regla 5 del plan).

    client_request_id: UUID generado por el cliente (POS offline) para
    reintentos idempotentes. Si ya existe, el servicio NO crea nada y
    devuelve la venta existente.

    fecha: fecha/hora de la venta. Debe ser <= ahora y no más de 72 horas
    atrás; si no, 422. Si viene fecha, venta.fecha y sus movimientos de
    inventario la usan. El folio sigue saliendo del servicio como siempre.
    """

    model_config = ConfigDict(extra="forbid")

    lineas: list[VentaDetalleCreate] = Field(min_length=1)
    descuento: Decimal = Field(default=Decimal("0"))
    metodo_pago: Literal["efectivo", "tarjeta", "transferencia", "otro"] = "efectivo"
    cliente_id: UUID | None = None
    client_request_id: UUID | None = None
    fecha: datetime | None = None

    @field_validator("descuento")
    @classmethod
    def _descuento_cuantizado_no_negativo(cls, valor: Decimal) -> Decimal:
        descuento = a_cuantia(valor)
        if descuento < 0:
            raise ValueError("El descuento no puede ser negativo")
        return descuento


class AnulacionCreate(BaseModel):
    """Motivo obligatorio de la anulación (la columna es NOT NULL al anular)."""

    model_config = ConfigDict(extra="forbid")

    motivo_anulacion: str

    @field_validator("motivo_anulacion")
    @classmethod
    def _motivo_no_vacio(cls, valor: str) -> str:
        motivo = valor.strip()
        if not motivo:
            raise ValueError("El motivo de la anulación es obligatorio")
        return motivo


class VentaDetalleRead(BaseModel):
    producto_id: UUID
    producto_nombre: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class VentaRead(BaseModel):
    id: UUID
    folio: str
    fecha: datetime
    cliente_id: UUID | None
    usuario_id: UUID
    metodo_pago: str
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    estado: str
    motivo_anulacion: str | None
    lineas: list[VentaDetalleRead]
    client_request_id: UUID | None = None


class ResumenVentaDia(BaseModel):
    """Un día del resumen de ventas, agrupado por fecha en hora de Guatemala."""

    fecha: date
    num_ventas: int
    total_vendido: Decimal


class ResumenVentas(BaseModel):
    """Respuesta de `GET /api/ventas/resumen` (panel del frontend)."""

    fecha_inicio: date
    fecha_fin: date
    num_ventas: int
    total_vendido: Decimal
    por_dia: list[ResumenVentaDia]