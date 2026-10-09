"""Crea (de forma idempotente) los usuarios de prueba propietario y padre.

Herramienta local: no es un endpoint y no se expone por HTTP.

- Da de alta la cuenta de acceso en Supabase Auth mediante la API Admin
  (`service_role`), porque la tabla `usuario` referencia `auth.users`.
- Registra/actualiza el perfil en la tabla `usuario` con el rol correspondiente.
- **No** crea al administrador: solo comprueba que exista uno activo e informa.

Los datos son de **PRUEBA** (P4): no son usuarios reales del negocio. La
contraseña por defecto es de prueba y puede sobreescribirse con la variable de
entorno `CONTRASENA_USUARIOS_PRUEBA`.

Requiere en `backend/.env`: `DATABASE_URL`, `SUPABASE_URL` y
`SUPABASE_SERVICE_ROLE_KEY`.
"""

import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

RAIZ_DEL_REPOSITORIO = Path(__file__).resolve().parents[1]
if str(RAIZ_DEL_REPOSITORIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_DEL_REPOSITORIO))

from app.core import config  # noqa: E402

CONTRASENA_POR_DEFECTO = "123456"

# email, nombre, rol
USUARIOS_DE_PRUEBA = [
    ("propietario@prueba.com", "SIMULACION Propietario (prueba)", "propietario"),
    ("padre@prueba.com", "SIMULACION Padre del dueño (prueba)", "padre"),
]

CREAR_USUARIO_AUTH = "/auth/v1/admin/users"
LISTAR_USUARIOS_AUTH = "/auth/v1/admin/users?page=1&per_page=1000"

UPSERT_PERFIL = text(
    """
    INSERT INTO usuario (auth_id, nombre, email, rol, activo)
    VALUES (:auth_id, :nombre, :email, :rol, true)
    ON CONFLICT (email) DO UPDATE SET
        auth_id = EXCLUDED.auth_id,
        nombre = EXCLUDED.nombre,
        rol = EXCLUDED.rol,
        activo = true
    RETURNING id
    """
)

CONTAR_ADMINISTRADORES = text(
    "SELECT count(*) FROM usuario WHERE rol = 'administrador' AND activo = true"
)


def _verificar_credenciales() -> None:
    if not config.SUPABASE_URL:
        raise SystemExit("Falta SUPABASE_URL en backend/.env")
    if not config.SUPABASE_SERVICE_ROLE_KEY:
        raise SystemExit("Falta SUPABASE_SERVICE_ROLE_KEY en backend/.env")
    if not config.DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en backend/.env")


def _peticion_admin(metodo: str, ruta: str, cuerpo: dict | None = None) -> dict:
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    peticion = urllib.request.Request(
        f"{config.SUPABASE_URL}{ruta}",
        data=datos,
        method=metodo,
        headers={
            "apikey": config.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(peticion) as respuesta:
            return json.loads(respuesta.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"Supabase Auth respondió {error.code}: {detalle}") from error


def _buscar_auth_id_por_email(email: str) -> str | None:
    respuesta = _peticion_admin("GET", LISTAR_USUARIOS_AUTH)
    for usuario in respuesta.get("users", []):
        if usuario.get("email", "").lower() == email.lower():
            return usuario.get("id")
    return None


def asegurar_usuario_auth(email: str, contrasena: str) -> str:
    try:
        creado = _peticion_admin(
            "POST",
            CREAR_USUARIO_AUTH,
            {"email": email, "password": contrasena, "email_confirm": True},
        )
        return creado["id"]
    except RuntimeError:
        existente = _buscar_auth_id_por_email(email)
        if existente is None:
            raise
        return existente


async def crear_usuarios() -> dict[str, int]:
    contrasena = os.getenv("CONTRASENA_USUARIOS_PRUEBA", CONTRASENA_POR_DEFECTO)

    auth_ids = {
        email: asegurar_usuario_auth(email, contrasena)
        for email, _nombre, _rol in USUARIOS_DE_PRUEBA
    }

    motor = create_async_engine(config.DATABASE_URL, pool_pre_ping=True)
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    resultado = {"perfiles": 0, "administradores": 0}

    async with fabrica() as sesion:
        async with sesion.begin():
            for email, nombre, rol in USUARIOS_DE_PRUEBA:
                await sesion.execute(
                    UPSERT_PERFIL,
                    {
                        "auth_id": auth_ids[email],
                        "nombre": nombre,
                        "email": email,
                        "rol": rol,
                    },
                )
                resultado["perfiles"] += 1
            resultado["administradores"] = (
                await sesion.execute(CONTAR_ADMINISTRADORES)
            ).scalar_one()

    await motor.dispose()
    return resultado


def main() -> None:
    _verificar_credenciales()
    resultado = asyncio.run(crear_usuarios())
    print("SIMULACION: usuarios ficticios de prueba, no son usuarios reales del negocio.")
    for email, _nombre, rol in USUARIOS_DE_PRUEBA:
        print(f"{rol}: {email}")
    print(f"perfiles asegurados: {resultado['perfiles']}")
    if resultado["administradores"] == 0:
        print("AVISO: no existe un administrador activo; créalo antes de usar la plataforma.")
    else:
        print(f"administradores activos: {resultado['administradores']}")


if __name__ == "__main__":
    main()
