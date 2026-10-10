from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import httpx2
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import simular_rol

from app.main import app

pytestmark = pytest.mark.integracion

DIA = datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)


async def _crear_venta(
    sesion: AsyncSession,
    usuario_id: UUID,
    folio: str,
    total: Decimal,
    fecha: datetime = DIA,
    estado: str = "activa",
) -> UUID:
    motivo = "Prueba de resumen" if estado == "anulada" else None
    return (
        await sesion.execute(
            text(
                """
                INSERT INTO venta (
                    folio, fecha, usuario_id, metodo_pago,
                    subtotal, descuento, total, estado, motivo_anulacion
                )
                VALUES (
                    :folio, :fecha, :usuario_id, 'efectivo',
                    :total, 0, :total, :estado, :motivo
                )
                RETURNING id
                """
            ),
            {
                "folio": folio,
                "fecha": fecha,
                "usuario_id": usuario_id,
                "total": total,
                "estado": estado,
                "motivo": motivo,
            },
        )
    ).scalar_one()


async def _obtener_resumen(
    sesion: AsyncSession, usuario_id: UUID, parametros: str = ""
) -> httpx2.Response:
    simular_rol(sesion, "propietario", usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app),
            base_url="http://pruebas",
        ) as cliente:
            return await cliente.get(f"/api/ventas/resumen{parametros}")
    finally:
        app.dependency_overrides.clear()


async def test_dias_sin_ventas_se_devuelven_en_cero(
    sesion_de_pruebas: AsyncSession,
    usuario_de_pruebas: UUID,
    almacen_de_pruebas: str,
) -> None:
    await _crear_venta(
        sesion_de_pruebas, usuario_de_pruebas, "F-2026-9001", Decimal("165.00")
    )

    respuesta = await _obtener_resumen(
        sesion_de_pruebas,
        usuario_de_pruebas,
        "?fecha_inicio=2026-03-09&fecha_fin=2026-03-11",
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["fecha_inicio"] == "2026-03-09"
    assert cuerpo["fecha_fin"] == "2026-03-11"
    assert cuerpo["num_ventas"] == 1
    assert cuerpo["total_vendido"] == "165.00"
    assert [dia["fecha"] for dia in cuerpo["por_dia"]] == [
        "2026-03-09",
        "2026-03-10",
        "2026-03-11",
    ]
    assert cuerpo["por_dia"][0]["num_ventas"] == 0
    assert cuerpo["por_dia"][0]["total_vendido"] == "0.00"
    assert cuerpo["por_dia"][1]["num_ventas"] == 1
    assert cuerpo["por_dia"][1]["total_vendido"] == "165.00"
    assert cuerpo["por_dia"][2]["num_ventas"] == 0
    assert cuerpo["por_dia"][2]["total_vendido"] == "0.00"


async def test_una_venta_anulada_no_cuenta(
    sesion_de_pruebas: AsyncSession,
    usuario_de_pruebas: UUID,
    almacen_de_pruebas: str,
) -> None:
    await _crear_venta(
        sesion_de_pruebas, usuario_de_pruebas, "F-2026-9002", Decimal("100.00")
    )
    await _crear_venta(
        sesion_de_pruebas,
        usuario_de_pruebas,
        "F-2026-9003",
        Decimal("250.00"),
        estado="anulada",
    )

    respuesta = await _obtener_resumen(
        sesion_de_pruebas,
        usuario_de_pruebas,
        "?fecha_inicio=2026-03-10&fecha_fin=2026-03-10",
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["num_ventas"] == 1
    assert cuerpo["total_vendido"] == "100.00"
    assert cuerpo["por_dia"][0]["num_ventas"] == 1
    assert cuerpo["por_dia"][0]["total_vendido"] == "100.00"


async def test_rango_invertido_devuelve_422(
    sesion_de_pruebas: AsyncSession,
    usuario_de_pruebas: UUID,
    almacen_de_pruebas: str,
) -> None:
    respuesta = await _obtener_resumen(
        sesion_de_pruebas,
        usuario_de_pruebas,
        "?fecha_inicio=2026-03-11&fecha_fin=2026-03-09",
    )

    assert respuesta.status_code == 422
    assert "fecha_fin" in respuesta.json()["detail"]
