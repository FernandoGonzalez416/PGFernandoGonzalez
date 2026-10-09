"""Pruebas unitarias de GET /api/me con capacidades (sin base de datos).

La autenticación se sustituye con `dependency_overrides`, así que no se valida
JWT ni se abre conexión a Postgres. El objetivo es comprobar que el endpoint
expone las capacidades derivadas del rol (P14), no reimplementarlas.
"""

from fastapi.testclient import TestClient

from app.core.capacidades import capacidades_de_rol
from app.core.security import UsuarioAutenticado, get_current_usuario
from app.main import app


def _pedir_me(rol: str):
    app.dependency_overrides[get_current_usuario] = lambda: UsuarioAutenticado(
        id="00000000-0000-0000-0000-0000000000a1",
        auth_id="00000000-0000-0000-0000-0000000000a2",
        nombre="Usuario de prueba",
        email="usuario@test.invalid",
        rol=rol,
        activo=True,
    )
    try:
        return TestClient(app).get("/api/me")
    finally:
        app.dependency_overrides.clear()


def test_responde_200_con_el_perfil_del_usuario():
    respuesta = _pedir_me("administrador")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["rol"] == "administrador"
    assert cuerpo["email"] == "usuario@test.invalid"


def test_padre_incluye_ventas_registrar_y_no_productos_editar():
    capacidades = _pedir_me("padre").json()["capacidades"]

    assert "ventas:registrar" in capacidades
    assert "productos:editar" not in capacidades


def test_administrador_incluye_usuarios_gestionar():
    capacidades = _pedir_me("administrador").json()["capacidades"]

    assert "usuarios:gestionar" in capacidades


def test_las_capacidades_coinciden_con_la_matriz_por_rol():
    for rol in ("administrador", "propietario", "padre"):
        assert _pedir_me(rol).json()["capacidades"] == capacidades_de_rol(rol)
