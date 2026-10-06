"""Fixtures compartidas de las pruebas del backend.

Decisión P20: las pruebas de integración usan un esquema `test` dentro del
mismo proyecto Supabase, con el DDL de `backend/tests/sql/00_test_schema.sql`.
Cada prueba corre dentro de una transacción que se revierte al terminar, así el
esquema `test` no acumula datos.

Si `DATABASE_URL_TEST` no está definida, las pruebas de integración se **omiten**
(`skip`); nunca se conectan por error a la base de desarrollo.

Las pruebas unitarias (capacidades, dinero, errores) no dependen de ninguna de
estas fixtures y corren sin base de datos.
"""

import os
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import config
from app.core.db import get_db_session
from app.core.security import UsuarioAutenticado, get_current_usuario
from app.main import app

# pytest no carga el .env por su cuenta; lo hacemos aquí para que
# DATABASE_URL_TEST pueda definirse en backend/.env (ignorado por git).
ARCHIVO_ENV = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ARCHIVO_ENV)

# `test` va primero para que los nombres de tabla sin calificar resuelvan al
# esquema de pruebas; `public` va después porque ahí vive `set_updated_at()`,
# que usan los triggers de `updated_at`.
ESQUEMA_PRUEBAS = "test"
RUTA_BUSQUEDA = f"{ESQUEMA_PRUEBAS}, public"
VARIABLE_ENTORNO = "DATABASE_URL_TEST"

MENSAJE_SIN_VARIABLE = (
    f"{VARIABLE_ENTORNO} no está definida: se omiten las pruebas de integración. "
    "Para habilitarlas, aplica backend/tests/sql/00_test_schema.sql y define "
    f"{VARIABLE_ENTORNO} en backend/.env."
)


@pytest.fixture
def url_de_pruebas() -> str:
    """Cadena de conexión del esquema de pruebas, o `skip` si no está definida."""
    url = os.environ.get(VARIABLE_ENTORNO, "").strip()
    if not url:
        pytest.skip(MENSAJE_SIN_VARIABLE)
    return url


@pytest_asyncio.fixture
async def sesion_de_pruebas(url_de_pruebas: str) -> AsyncIterator[AsyncSession]:
    """Sesión cuya transacción se revierte al terminar cada prueba.

    El motor se crea por prueba, no por sesión, para no compartir conexiones
    entre pruebas y no arrastrar un bucle de eventos de otro ámbito. El
    `search_path` se fija al abrir la conexión con `server_settings`, así que
    aplica a cualquier consulta de la sesión.

    El DDL **no** se aplica aquí a propósito: `00_test_schema.sql` se aplica una
    vez de forma manual, para que el esquema refleje el archivo versionado y no
    una copia escondida en el fixture.
    """
    motor = create_async_engine(
        url_de_pruebas,
        connect_args={"server_settings": {"search_path": RUTA_BUSQUEDA}},
    )
    try:
        async with motor.connect() as conexion:
            transaccion = await conexion.begin()
            try:
                tabla = await conexion.scalar(text("SELECT to_regclass('categoria')::text"))
                if tabla is None:
                    pytest.fail(
                        "No se encontró la tabla `categoria` en el esquema "
                        f"`{ESQUEMA_PRUEBAS}` con la ruta de búsqueda `{RUTA_BUSQUEDA}`. "
                        "Aplica backend/tests/sql/00_test_schema.sql a "
                        f"{VARIABLE_ENTORNO}, o corrige la URL para que apunte a "
                        "ese esquema."
                    )

                maker = async_sessionmaker(
                    bind=conexion,
                    expire_on_commit=False,
                    class_=AsyncSession,
                )
                async with maker() as sesion:
                    yield sesion
            finally:
                await transaccion.rollback()
    finally:
        await motor.dispose()


@pytest_asyncio.fixture
async def almacen_de_pruebas(sesion_de_pruebas: AsyncSession) -> str:
    """Almacén por defecto dentro de la transacción de la prueba.

    `existencia.almacen_id` es NOT NULL, así que cualquier prueba que escriba
    existencias necesita uno. La fila se inserta en la misma transacción que se
    revierte al terminar, por lo que no deja rastro.
    """
    nombre = config.ALMACEN_PREDETERMINADO
    await sesion_de_pruebas.execute(
        text("INSERT INTO almacen (nombre) VALUES (:nombre) ON CONFLICT DO NOTHING"),
        {"nombre": nombre},
    )
    return nombre


@pytest_asyncio.fixture
async def usuario_de_pruebas(sesion_de_pruebas: AsyncSession) -> UUID:
    """Usuario propietario válido dentro de la transacción de la prueba.

    `usuario.auth_id` referencia `auth.users`, así que hay que insertar primero
    la fila en `auth.users` (mismo aviso que hace el propio
    `tests/sql/00_test_schema.sql`). `auth.users` solo exige `id` NOT NULL sin
    valor por defecto; el resto de columnas son aceptables o tienen default.

    Al vivir dentro de la transacción que el fixture revierte, ni `auth.users`
    ni `usuario` conservan la fila al terminar la prueba.
    """
    auth_id = uuid4()
    await sesion_de_pruebas.execute(
        text("INSERT INTO auth.users (id) VALUES (:auth_id)"), {"auth_id": auth_id}
    )
    usuario_id = (
        await sesion_de_pruebas.execute(
            text(
                """
                INSERT INTO usuario (auth_id, nombre, email, rol)
                VALUES (:auth_id, 'Usuario de prueba', 'prueba@test.invalid', 'propietario')
                RETURNING id
                """
            ),
            {"auth_id": auth_id},
        )
    ).scalar_one()
    return usuario_id

def simular_rol(sesion: AsyncSession, rol: str, usuario_id: UUID | None = None) -> None:
    """Sustituye autenticación y sesión para que la app vea al usuario con `rol`.

    Solo existe un usuario administrador real en la base, así que los demás roles
    se simulan (P14). No hace falta JWT: `get_current_usuario` sustituida nunca
    llega a validar el token.

    `usuario_id` permite apuntar a una fila real de `usuario` cuando la
    operación escribe (los `INSERT` con FK a `usuario` fallan con el id fijo
    por defecto, que no existe en el esquema de pruebas).

    El llamador limpia `app.dependency_overrides` al terminar su bloque try/finally.
    """

    identidad = usuario_id or UUID("00000000-0000-0000-0000-0000000000a1")

    async def _sesion():
        yield sesion

    app.dependency_overrides[get_db_session] = _sesion
    app.dependency_overrides[get_current_usuario] = lambda: UsuarioAutenticado(
        id=str(identidad),
        auth_id="00000000-0000-0000-0000-0000000000a2",
        nombre="Usuario de prueba",
        email="usuario@test.invalid",
        rol=rol,
        activo=True,
    )
