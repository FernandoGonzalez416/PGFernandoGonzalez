"""Excepciones de dominio de la plataforma.

Ninguna excepción de este módulo conoce HTTP: el código de estado se decide en
un único lugar, el manejador global registrado en `app/main.py`. Los servicios
lanzan estas excepciones y no construyen `HTTPException`.

Dos familias agrupan los casos que se repiten:

- `EntidadNoEncontradaError`: el recurso solicitado no existe (404).
- `ConflictoDeUnicidadError`: una restricción UNIQUE del esquema fue violada (409).
"""

from sqlalchemy.exc import IntegrityError


class ErrorDeDominio(Exception):
    """Base de todo error de negocio de la plataforma."""

    def __init__(self, mensaje: str) -> None:
        self.mensaje = mensaje
        super().__init__(mensaje)


class EntidadNoEncontradaError(ErrorDeDominio):
    """El recurso solicitado no existe."""


class ProductoNoEncontradoError(EntidadNoEncontradaError):
    def __init__(self, producto_id: str) -> None:
        super().__init__(f"No existe un producto con id '{producto_id}'")


class CategoriaNoEncontradaError(EntidadNoEncontradaError):
    def __init__(self, categoria_id: str) -> None:
        super().__init__(f"No existe una categoría con id '{categoria_id}'")


class ProveedorNoEncontradoError(EntidadNoEncontradaError):
    def __init__(self, proveedor_id: str) -> None:
        super().__init__(f"No existe un proveedor con id '{proveedor_id}'")


class ConflictoDeUnicidadError(ErrorDeDominio):
    """Una restricción UNIQUE del esquema fue violada."""


class CodigoProductoDuplicadoError(ConflictoDeUnicidadError):
    def __init__(self, codigo: str) -> None:
        super().__init__(f"Ya existe un producto con el código '{codigo}'")


class CategoriaDuplicadaError(ConflictoDeUnicidadError):
    def __init__(self, nombre: str) -> None:
        super().__init__(f"Ya existe una categoría con el nombre '{nombre}'")


class ProductoConExistenciasError(ErrorDeDominio):
    """El producto tiene existencias o ventas y no puede desactivarse."""


class VencimientoInvalidoError(ErrorDeDominio):
    """La fecha de vencimiento enviada no es admisible."""


def _menciona_restriccion(error: IntegrityError, nombre: str) -> bool:
    """¿La violación de integridad corresponde a la restricción `nombre`?

    psycopg expone `constraint_name` como atributo, pero asyncpg —el driver que
    usa el proyecto— no lo tiene y solo lo incluye en el mensaje. Se revisan
    ambos para no atar la traducción de errores al driver.
    """
    if getattr(error.orig, "constraint_name", None) == nombre:
        return True
    return f'"{nombre}"' in str(error.orig)