"""Pruebas unitarias de CORS (sin base de datos).

El middleware de CORS es configurable por entorno (`CORS_ORIGINS`). Estas
pruebas verifican que el origen del frontend de desarrollo queda permitido y
que un origen ajeno no recibe la cabecera de permiso.
"""

from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)
ORIGEN_VITE = "http://localhost:5173"
ORIGEN_VITE_127 = "http://127.0.0.1:5173"


def test_preflight_del_origen_del_frontend_es_permitido():
    respuesta = cliente.options(
        "/api/productos",
        headers={
            "Origin": ORIGEN_VITE,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.headers.get("access-control-allow-origin") == ORIGEN_VITE


def test_peticion_simple_lleva_la_cabecera_del_origen_permitido():
    respuesta = cliente.get("/health", headers={"Origin": ORIGEN_VITE_127})

    assert respuesta.status_code == 200
    assert respuesta.headers.get("access-control-allow-origin") == ORIGEN_VITE_127


def test_origen_ajeno_no_recibe_cabecera_de_permiso():
    respuesta = cliente.options(
        "/api/productos",
        headers={
            "Origin": "http://malicioso.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in respuesta.headers
