import re
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.folio import generar_folio

pytestmark = pytest.mark.integracion


async def _anio(sesion: AsyncSession) -> int:
    return (
        await sesion.execute(text("SELECT EXTRACT(YEAR FROM now())::int"))
    ).scalar_one()


async def _sembrar_venta(sesion: AsyncSession, folio: str, usuario_id: UUID) -> None:
    await sesion.execute(
        text(
            """
            INSERT INTO venta (folio, usuario_id, metodo_pago, subtotal, descuento, total)
            VALUES (:folio, :usuario_id, 'efectivo', 10.00, 0.00, 10.00)
            """
        ),
        {"folio": folio, "usuario_id": usuario_id},
    )


class TestFolio:
    async def test_primera_venta_del_anio_da_folio_0001(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
    ) -> None:
        folio = await generar_folio(sesion_de_pruebas)

        assert folio == f"F-{await _anio(sesion_de_pruebas)}-0001"
        assert re.fullmatch(r"^F-\d{4}-\d{4,}$", folio)

    async def test_incrementa_sobre_el_ultimo_folio_existente(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
    ) -> None:
        await _sembrar_venta(
            sesion_de_pruebas,
            f"F-{await _anio(sesion_de_pruebas)}-0003",
            usuario_de_pruebas,
        )

        assert (
            await generar_folio(sesion_de_pruebas)
            == f"F-{await _anio(sesion_de_pruebas)}-0004"
        )

    async def test_lpad_a_cuatro_digitos(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
    ) -> None:
        await _sembrar_venta(
            sesion_de_pruebas,
            f"F-{await _anio(sesion_de_pruebas)}-0009",
            usuario_de_pruebas,
        )

        assert (
            await generar_folio(sesion_de_pruebas)
            == f"F-{await _anio(sesion_de_pruebas)}-0010"
        )

    async def test_mas_de_cuatro_digitos_sigue_siendo_valido(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
    ) -> None:
        await _sembrar_venta(
            sesion_de_pruebas,
            f"F-{await _anio(sesion_de_pruebas)}-9999",
            usuario_de_pruebas,
        )

        folio = await generar_folio(sesion_de_pruebas)
        assert folio == f"F-{await _anio(sesion_de_pruebas)}-10000"
        assert re.fullmatch(r"^F-\d{4}-\d{4,}$", folio)

    async def test_folio_de_otro_anio_no_influye(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
    ) -> None:
        await _sembrar_venta(sesion_de_pruebas, "F-2020-0042", usuario_de_pruebas)

        assert (
            await generar_folio(sesion_de_pruebas)
            == f"F-{await _anio(sesion_de_pruebas)}-0001"
        )