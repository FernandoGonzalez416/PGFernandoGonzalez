"""Pruebas del aislamiento del esquema `test` (P20).

Verifican que la sesión de integración apunta al esquema `test`, que este
replica las 13 tablas del esquema de la aplicación, y que los datos de prueba
**no** tocan el esquema `public`. La última es la razón de existir del esquema
separado: si se escribiera en `public` se estaría probando sobre los datos del
piloto.

Todas se omiten si `DATABASE_URL_TEST` no está definida. Los datos insertados
son ficticios y están etiquetados como simulación (P4).
"""

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integracion

TOTAL_TABLES_ESPERADAS = 13


async def test_la_conexion_resuelve_las_tablas_al_esquema_test(sesion_de_pruebas):
    esquema_actual = await sesion_de_pruebas.scalar(text("SELECT current_schema()"))
    assert esquema_actual == "test"

    tabla_sin_calificar = await sesion_de_pruebas.scalar(
        text("SELECT to_regclass('producto')::text")
    )
    tabla_explicita = await sesion_de_pruebas.scalar(
        text("SELECT to_regclass('test.producto')::text")
    )
    assert tabla_sin_calificar is not None
    assert tabla_sin_calificar == tabla_explicita


async def test_el_esquema_test_replica_las_trece_tablas(sesion_de_pruebas):
    resultado = await sesion_de_pruebas.execute(
        text(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'test' AND table_type = 'BASE TABLE'"
        )
    )
    assert resultado.scalar_one() == TOTAL_TABLES_ESPERADAS


async def test_las_pruebas_no_dejan_rastro_entre_ejecuciones(sesion_de_pruebas):
    antes = await sesion_de_pruebas.scalar(text("SELECT count(*) FROM categoria"))
    await sesion_de_pruebas.execute(
        text(
            "INSERT INTO categoria (nombre, descripcion) "
            "VALUES (:nombre, :descripcion)"
        ),
        {
            "nombre": "Categoría de prueba (simulación)",
            "descripcion": "Dato ficticio insertado por una prueba de integración",
        },
    )
    despues = await sesion_de_pruebas.scalar(text("SELECT count(*) FROM categoria"))
    assert despues == antes + 1


async def test_escribir_en_el_esquema_test_no_toca_public(sesion_de_pruebas):
    public_antes = await sesion_de_pruebas.scalar(
        text("SELECT count(*) FROM public.categoria")
    )
    test_antes = await sesion_de_pruebas.scalar(
        text("SELECT count(*) FROM test.categoria")
    )

    await sesion_de_pruebas.execute(
        text("INSERT INTO categoria (nombre) VALUES (:nombre)"),
        {"nombre": "Aislamiento (simulación)"},
    )

    test_despues = await sesion_de_pruebas.scalar(
        text("SELECT count(*) FROM test.categoria")
    )
    public_despues = await sesion_de_pruebas.scalar(
        text("SELECT count(*) FROM public.categoria")
    )

    assert test_despues == test_antes + 1
    assert public_despues == public_antes