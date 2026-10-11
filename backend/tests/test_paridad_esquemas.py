"""Paridad de esquemas public/test (M1, P20).

Las 13 tablas de la aplicación deben exponer las mismas columnas en ambos
esquemas: (table_name, column_name, data_type, is_nullable). Si falta una
tabla o difiere alguna columna, la prueba falla listando cada diferencia.
No se ajusta la prueba para esconder diferencias: se corrige el DDL
(`supabase/migrations/*` o `backend/tests/sql/00_test_schema.sql`).

Se omite si `DATABASE_URL_TEST` no está definida (P20).
"""

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integracion

TABLAS_APLICACION = [
    "almacen",
    "categoria",
    "cliente",
    "detalle_venta",
    "existencia",
    "movimiento_inventario",
    "notificacion",
    "prediccion",
    "producto",
    "proveedor",
    "sugerencia",
    "usuario",
    "venta",
]


async def _columnas(sesion, esquema: str, tabla: str) -> list[tuple]:
    filas = await sesion.execute(
        text(
            "SELECT table_name, column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema = :esquema AND table_name = :tabla "
            "ORDER BY ordinal_position"
        ),
        {"esquema": esquema, "tabla": tabla},
    )
    return [tuple(f) for f in filas.all()]


async def test_paridad_columnas_entre_public_y_test(sesion_de_pruebas):
    diferencias: list[str] = []
    for tabla in TABLAS_APLICACION:
        en_public = await _columnas(sesion_de_pruebas, "public", tabla)
        en_test = await _columnas(sesion_de_pruebas, "test", tabla)
        if not en_public:
            diferencias.append(f"tabla ausente en public: {tabla}")
            continue
        if not en_test:
            diferencias.append(f"tabla ausente en test: {tabla}")
            continue
        solo_public = sorted(set(en_public) - set(en_test))
        solo_test = sorted(set(en_test) - set(en_public))
        for columna in solo_public:
            diferencias.append(f"solo en public.{tabla}: {columna}")
        for columna in solo_test:
            diferencias.append(f"solo en test.{tabla}: {columna}")
    assert not diferencias, (
        "Paridad public/test rota:\n" + "\n".join(diferencias)
    )
