"""Pruebas de integración: idempotencia y fecha del POS offline (P27/F5).

Requieren `DATABASE_URL_TEST` y el esquema `test` aplicado (P20); se omiten si
falta la variable. Reutilizan los ayudantes de `test_ventas.py` para no duplicar
el armado de productos, ventas y movimientos.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from test_ventas import _cantidad, _crear_producto, _linea, _movimientos, _post_venta

pytestmark = pytest.mark.integracion


async def test_misma_peticion_dos_veces_devuelve_la_misma_venta(
    sesion_de_pruebas: AsyncSession,
    usuario_de_pruebas: UUID,
    almacen_de_pruebas: str,
) -> None:
    """Misma client_request_id dos veces → 201 y luego 200, sin duplicar nada."""
    producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
    crid = str(uuid4())
    cuerpo = {"lineas": [_linea(producto_id, 2)], "client_request_id": crid}

    primera = await _post_venta(
        sesion_de_pruebas, "propietario", usuario_de_pruebas, cuerpo
    )
    assert primera.status_code == 201, primera.text
    assert primera.json()["client_request_id"] == crid

    repetida = await _post_venta(
        sesion_de_pruebas, "propietario", usuario_de_pruebas, cuerpo
    )
    assert repetida.status_code == 200, repetida.text
    assert repetida.json()["id"] == primera.json()["id"]
    assert repetida.json()["folio"] == primera.json()["folio"]

    # El stock se descontó una sola vez y hay un único movimiento de salida.
    assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("8.00")
    salidas = [
        m
        for m in await _movimientos(sesion_de_pruebas, producto_id)
        if m["tipo"] == "salida"
    ]
    assert len(salidas) == 1

    # Una sola fila de venta con ese folio.
    total = (
        await sesion_de_pruebas.execute(
            text("SELECT count(*) FROM venta WHERE folio = :folio"),
            {"folio": primera.json()["folio"]},
        )
    ).scalar_one()
    assert total == 1


async def test_ids_distintos_crean_ventas_distintas(
    sesion_de_pruebas: AsyncSession,
    usuario_de_pruebas: UUID,
    almacen_de_pruebas: str,
) -> None:
    """Dos client_request_id distintos → dos ventas independientes."""
    producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)

    primera = await _post_venta(
        sesion_de_pruebas,
        "propietario",
        usuario_de_pruebas,
        {"lineas": [_linea(producto_id, 1)], "client_request_id": str(uuid4())},
    )
    segunda = await _post_venta(
        sesion_de_pruebas,
        "propietario",
        usuario_de_pruebas,
        {"lineas": [_linea(producto_id, 1)], "client_request_id": str(uuid4())},
    )

    assert primera.status_code == 201, primera.text
    assert segunda.status_code == 201, segunda.text
    assert primera.json()["folio"] != segunda.json()["folio"]


async def test_fecha_futura_devuelve_422(
    sesion_de_pruebas: AsyncSession,
    usuario_de_pruebas: UUID,
    almacen_de_pruebas: str,
) -> None:
    """Una fecha posterior a ahora se rechaza con 422."""
    producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
    fecha = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

    respuesta = await _post_venta(
        sesion_de_pruebas,
        "propietario",
        usuario_de_pruebas,
        {"lineas": [_linea(producto_id, 1)], "fecha": fecha},
    )

    assert respuesta.status_code == 422, respuesta.text
    assert "posterior" in respuesta.json()["detail"]


async def test_fecha_mas_de_72h_atras_devuelve_422(
    sesion_de_pruebas: AsyncSession,
    usuario_de_pruebas: UUID,
    almacen_de_pruebas: str,
) -> None:
    """Una fecha anterior a 72 horas se rechaza con 422."""
    producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
    fecha = (datetime.now(timezone.utc) - timedelta(hours=73)).isoformat()

    respuesta = await _post_venta(
        sesion_de_pruebas,
        "propietario",
        usuario_de_pruebas,
        {"lineas": [_linea(producto_id, 1)], "fecha": fecha},
    )

    assert respuesta.status_code == 422, respuesta.text
    assert "72 horas" in respuesta.json()["detail"]


async def test_fecha_valida_queda_guardada(
    sesion_de_pruebas: AsyncSession,
    usuario_de_pruebas: UUID,
    almacen_de_pruebas: str,
) -> None:
    """Una fecha válida (una hora atrás) se guarda como fecha de la venta."""
    producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
    enviada = datetime.now(timezone.utc) - timedelta(hours=1)

    respuesta = await _post_venta(
        sesion_de_pruebas,
        "propietario",
        usuario_de_pruebas,
        {"lineas": [_linea(producto_id, 1)], "fecha": enviada.isoformat()},
    )

    assert respuesta.status_code == 201, respuesta.text
    fecha_guardada = (
        await sesion_de_pruebas.execute(
            text("SELECT fecha FROM venta WHERE id = :venta_id"),
            {"venta_id": respuesta.json()["id"]},
        )
    ).scalar_one()
    assert abs((fecha_guardada - enviada).total_seconds()) < 1


async def test_fecha_sin_zona_horaria_se_interpreta_como_utc(
    sesion_de_pruebas: AsyncSession,
    usuario_de_pruebas: UUID,
    almacen_de_pruebas: str,
) -> None:
    """Un cliente que no envía zona horaria no rompe la validación (naive → UTC)."""
    producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
    enviada = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(tzinfo=None)

    respuesta = await _post_venta(
        sesion_de_pruebas,
        "propietario",
        usuario_de_pruebas,
        {"lineas": [_linea(producto_id, 1)], "fecha": enviada.isoformat()},
    )

    assert respuesta.status_code == 201, respuesta.text


async def test_sin_client_request_id_crea_venta_normal(
    sesion_de_pruebas: AsyncSession,
    usuario_de_pruebas: UUID,
    almacen_de_pruebas: str,
) -> None:
    """Sin client_request_id la venta se crea con normalidad (201)."""
    producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)

    respuesta = await _post_venta(
        sesion_de_pruebas,
        "propietario",
        usuario_de_pruebas,
        {"lineas": [_linea(producto_id, 1)]},
    )

    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["client_request_id"] is None
