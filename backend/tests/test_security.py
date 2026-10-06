"""Pruebas de autenticación (get_current_usuario) y de autorización (requiere).

Todos los datos son FICTICIOS y locales: las llaves EC se generan en memoria y
los tokens se firman aquí mismo. No se usa el JWT ni las claves reales del
proyecto, y no se abre conexión a Postgres ni a Supabase: el JWKS y la sesión
de base de datos se sustituyen por dobles de prueba.
"""

import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.capacidades import Capacidad
from app.core.permissions import requiere
from app.core.security import (
    LEEWAY_SEGUNDOS,
    UsuarioAutenticado,
    get_current_usuario,
)

KID_PRUEBA = "kid-de-prueba"
AUTH_ID_PRUEBA = uuid.UUID("11111111-1111-4111-8111-111111111111")
USUARIO_ID_PRUEBA = uuid.UUID("22222222-2222-4222-8222-222222222222")

# Distingue "sin fila en la tabla" (None) de "usar la fila de ejemplo".
_SIN_FILA = object()


@pytest.fixture(scope="module")
def llave_privada():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="module")
def llave_publica(llave_privada):
    return llave_privada.public_key()


@pytest.fixture
def cliente_jwks(llave_publica):
    return ClienteJWKSFalso(llave_publica)


def _ahora():
    return datetime.now(timezone.utc)


def _crear_token(llave_privada, **overrides):
    payload = {
        "sub": str(AUTH_ID_PRUEBA),
        "aud": "authenticated",
        "role": "authenticated",
        "email": "usuario.prueba@example.com",
        "iat": _ahora(),
        "exp": _ahora() + timedelta(hours=1),
    }
    payload.update(overrides)
    return jwt.encode(payload, llave_privada, algorithm="ES256", headers={"kid": KID_PRUEBA})


def _crear_token_hs256(**overrides):
    payload = {
        "sub": str(AUTH_ID_PRUEBA),
        "aud": "authenticated",
        "iat": _ahora(),
        "exp": _ahora() + timedelta(hours=1),
    }
    payload.update(overrides)
    return jwt.encode(payload, "clave-simetrica-de-prueba-solo-para-tests", algorithm="HS256")


def _crear_token_sin_firma(**overrides):
    def segmento(datos):
        crudo = json.dumps(datos).encode()
        return base64.urlsafe_b64encode(crudo).rstrip(b"=")

    payload = {"sub": str(AUTH_ID_PRUEBA), "aud": "authenticated"}
    payload.update(overrides)
    return (
        segmento({"alg": "none", "typ": "JWT"}) + b"." + segmento(payload) + b"."
    ).decode()


def _fila(**overrides):
    fila = {
        "id": USUARIO_ID_PRUEBA,
        "auth_id": AUTH_ID_PRUEBA,
        "nombre": "Usuario de prueba",
        "email": "usuario.prueba@example.com",
        "rol": "administrador",
        "activo": True,
    }
    fila.update(overrides)
    return fila


class ClienteJWKSFalso:
    """Sustituye a jwt.PyJWKClient: devuelve la llave pública local sin red."""

    def __init__(self, clave_publica):
        self._clave = clave_publica
        self.kids_solicitados = []

    def get_signing_key_from_jwt(self, token):
        self.kids_solicitados.append(jwt.get_unverified_header(token).get("kid"))
        return SimpleNamespace(key=self._clave, key_id=KID_PRUEBA)


class _MappingsFalso:
    def __init__(self, fila):
        self._fila = fila

    def first(self):
        return self._fila


class _ResultadoFalso:
    def __init__(self, fila):
        self._fila = fila

    def mappings(self):
        return _MappingsFalso(self._fila)


class SesionFalsa:
    """Doble de AsyncSession: registra los parámetros de cada consulta."""

    def __init__(self, fila):
        self.fila = fila
        self.consultas = []

    async def execute(self, statement, parametros):
        self.consultas.append(parametros)
        return _ResultadoFalso(self.fila)


async def _autenticar(token, cliente_jwks, fila=_SIN_FILA):
    sesion = SesionFalsa(_fila() if fila is _SIN_FILA else fila)
    with patch("app.core.security.get_jwks_client", return_value=cliente_jwks):
        usuario = await get_current_usuario(
            credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            db=sesion,
        )
    return usuario, sesion


def _usuario_autenticado(rol):
    return UsuarioAutenticado(
        id=str(USUARIO_ID_PRUEBA),
        auth_id=str(AUTH_ID_PRUEBA),
        nombre="Usuario de prueba",
        email="usuario.prueba@example.com",
        rol=rol,
        activo=True,
    )


class TestGetCurrentUsuarioAceptado:
    async def test_token_es256_valido_devuelve_el_usuario_activo(
        self, llave_privada, cliente_jwks
    ):
        usuario, sesion = await _autenticar(_crear_token(llave_privada), cliente_jwks)

        assert usuario.nombre == "Usuario de prueba"
        assert usuario.email == "usuario.prueba@example.com"
        assert usuario.rol == "administrador"
        assert usuario.activo is True

    async def test_los_uuid_de_la_fila_se_entregan_como_texto(
        self, llave_privada, cliente_jwks
    ):
        usuario, _ = await _autenticar(_crear_token(llave_privada), cliente_jwks)

        assert usuario.id == str(USUARIO_ID_PRUEBA)
        assert usuario.auth_id == str(AUTH_ID_PRUEBA)

    async def test_busca_la_fila_por_el_sub_del_token(
        self, llave_privada, cliente_jwks
    ):
        _, sesion = await _autenticar(_crear_token(llave_privada), cliente_jwks)

        assert sesion.consultas == [{"auth_id": str(AUTH_ID_PRUEBA)}]

    async def test_acepta_token_emitido_por_adelanto_por_desfase_de_reloj(
        self, llave_privada, cliente_jwks
    ):
        """El reloj de Supabase puede ir adelantado: el margen debe tolerarlo."""
        token = _crear_token(
            llave_privada,
            iat=_ahora() + timedelta(seconds=LEEWAY_SEGUNDOS - 10),
            exp=_ahora() + timedelta(hours=1),
        )

        usuario, _ = await _autenticar(token, cliente_jwks)

        assert usuario.auth_id == str(AUTH_ID_PRUEBA)


class TestGetCurrentUsuarioRechazado:
    async def test_algoritmo_hs256_es_rechazado(self, cliente_jwks):
        with pytest.raises(HTTPException) as error:
            await _autenticar(_crear_token_hs256(), cliente_jwks)

        assert error.value.status_code == 401
        assert "HS256" in error.value.detail

    async def test_algoritmo_hs256_no_consulta_la_llave_ni_la_base_de_datos(
        self, cliente_jwks
    ):
        """Confusion de algoritmos: no se busca llave ni se toca la BD."""
        with pytest.raises(HTTPException):
            await _autenticar(_crear_token_hs256(), cliente_jwks)

        assert cliente_jwks.kids_solicitados == []

    async def test_algoritmo_none_es_rechazado(self, cliente_jwks):
        with pytest.raises(HTTPException) as error:
            await _autenticar(_crear_token_sin_firma(), cliente_jwks)

        assert error.value.status_code == 401
        assert "none" in error.value.detail

    async def test_firma_invalida_es_rechazada(self, cliente_jwks):
        otra_llave = ec.generate_private_key(ec.SECP256R1())
        token = _crear_token(otra_llave)

        with pytest.raises(HTTPException) as error:
            await _autenticar(token, cliente_jwks)

        assert error.value.status_code == 401
        assert error.value.detail == "Token inválido o expirado, inicia sesión de nuevo"

    async def test_token_expirado_es_rechazado(self, llave_privada, cliente_jwks):
        token = _crear_token(
            llave_privada,
            iat=_ahora() - timedelta(hours=2),
            exp=_ahora() - timedelta(seconds=LEEWAY_SEGUNDOS + 60),
        )

        with pytest.raises(HTTPException) as error:
            await _autenticar(token, cliente_jwks)

        assert error.value.status_code == 401

    async def test_audiencia_incorrecta_es_rechazada(self, llave_privada, cliente_jwks):
        token = _crear_token(llave_privada, aud="otra-audiencia")

        with pytest.raises(HTTPException) as error:
            await _autenticar(token, cliente_jwks)

        assert error.value.status_code == 401

    async def test_token_sin_sub_es_rechazado(self, llave_privada, cliente_jwks):
        token = _crear_token(llave_privada, sub="")

        with pytest.raises(HTTPException) as error:
            await _autenticar(token, cliente_jwks)

        assert error.value.status_code == 401
        assert error.value.detail == "Token sin sub"

    async def test_usuario_sin_fila_en_la_tabla_usuario_es_403(
        self, llave_privada, cliente_jwks
    ):
        with pytest.raises(HTTPException) as error:
            await _autenticar(_crear_token(llave_privada), cliente_jwks, fila=None)

        assert error.value.status_code == 403
        assert error.value.detail == "Usuario sin perfil registrado"

    async def test_usuario_inactivo_es_403(self, llave_privada, cliente_jwks):
        with pytest.raises(HTTPException) as error:
            await _autenticar(
                _crear_token(llave_privada), cliente_jwks, fila=_fila(activo=False)
            )

        assert error.value.status_code == 403
        assert error.value.detail == "Usuario inactivo"


class TestRequiereCapacidad:
    def test_rol_con_la_capacidad_recibe_el_usuario(self):
        usuario = _usuario_autenticado("administrador")

        resultado = requiere(Capacidad.PRODUCTOS_EDITAR)(usuario)

        assert resultado is usuario

    def test_padre_puede_registrar_ventas(self):
        usuario = _usuario_autenticado("padre")

        resultado = requiere(Capacidad.VENTAS_REGISTRAR)(usuario)

        assert resultado is usuario

    def test_padre_no_puede_editar_productos(self):
        with pytest.raises(HTTPException) as error:
            requiere(Capacidad.PRODUCTOS_EDITAR)(_usuario_autenticado("padre"))

        assert error.value.status_code == 403
        assert error.value.detail == (
            "El rol 'padre' no tiene la capacidad 'productos:editar'"
        )

    def test_padre_no_puede_gestionar_usuarios(self):
        with pytest.raises(HTTPException) as error:
            requiere(Capacidad.USUARIOS_GESTIONAR)(_usuario_autenticado("padre"))

        assert error.value.status_code == 403

    def test_padre_no_puede_ver_prediccion(self):
        with pytest.raises(HTTPException) as error:
            requiere(Capacidad.PREDICCION_VER)(_usuario_autenticado("padre"))

        assert error.value.status_code == 403

    def test_padre_no_puede_ver_reportes(self):
        with pytest.raises(HTTPException) as error:
            requiere(Capacidad.REPORTES_VER)(_usuario_autenticado("padre"))

        assert error.value.status_code == 403

    def test_propietario_no_puede_gestionar_usuarios(self):
        with pytest.raises(HTTPException) as error:
            requiere(Capacidad.USUARIOS_GESTIONAR)(_usuario_autenticado("propietario"))

        assert error.value.status_code == 403
