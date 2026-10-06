from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.dinero import a_cuantia


class ExistenciaRead(BaseModel):
    producto_id: UUID
    almacen_id: UUID
    almacen_nombre: str
    cantidad: Decimal
    updated_at: datetime


class ExistenciaAjuste(BaseModel):
    """Ajuste de stock de un producto en el almacén por defecto (P19).

    `cantidad` es un **delta con signo**: positivo suma, negativo resta. El
    signo no se guarda en `movimiento_inventario.cantidad` porque su CHECK
    exige `cantidad > 0`; se materializa en `movimiento_inventario.tipo`
    (`entrada` al subir, `salida` al bajar) con `referencia_tipo='ajuste'`,
    de modo que la bitácora sigue reconstruible sin ambigüedad.
    """

    model_config = ConfigDict(extra="forbid")

    producto_id: UUID
    cantidad: Decimal
    nota: str

    @field_validator("cantidad")
    @classmethod
    def _cantidad_no_nula(cls, valor: Decimal) -> Decimal:
        cuantia = a_cuantia(valor)
        if cuantia == 0:
            raise ValueError("El ajuste no puede ser cero: no habría nada que corregir")
        return cuantia

    @field_validator("nota")
    @classmethod
    def _nota_no_vacia(cls, valor: str) -> str:
        nota = valor.strip()
        if not nota:
            raise ValueError("La nota del ajuste es obligatoria")
        return nota
