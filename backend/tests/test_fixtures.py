from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integracion


async def test_el_fixture_de_usuario_es_valido(
    sesion_de_pruebas: AsyncSession, usuario_de_pruebas: UUID
) -> None:
    fila = (
        await sesion_de_pruebas.execute(
            text("SELECT auth_id, nombre, email, rol, activo FROM usuario WHERE id = :id"),
            {"id": usuario_de_pruebas},
        )
    ).mappings().one()
    assert fila["rol"] == "propietario"
    assert fila["activo"] is True

    existe_auth = (
        await sesion_de_pruebas.execute(
            text("SELECT 1 FROM auth.users WHERE id = :auth_id"),
            {"auth_id": fila["auth_id"]},
        )
    ).scalar_one_or_none()
    assert existe_auth is not None


async def test_el_fixture_de_almacen_es_valido(
    sesion_de_pruebas: AsyncSession, almacen_de_pruebas: str
) -> None:
    total = (
        await sesion_de_pruebas.execute(
            text("SELECT count(*) FROM almacen WHERE nombre = :nombre"),
            {"nombre": almacen_de_pruebas},
        )
    ).scalar_one()
    assert total == 1