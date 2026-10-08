import pytest
from fastapi import status
import httpx2

from app.main import app
from conftest import simular_rol


pytestmark = pytest.mark.integracion


async def _peticion_alertas(sesion, rol=None, usuario_id=None):
    if rol is not None:
        simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app),
            base_url='http://test',
        ) as ac:
            return await ac.get('/api/alertas/')
    finally:
        app.dependency_overrides.clear()


async def _peticion_reportes(sesion, rol=None, usuario_id=None):
    if rol is not None:
        simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app),
            base_url='http://test',
        ) as ac:
            return await ac.get('/api/reportes/productos-mas-vendidos')
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_alertas_sin_token(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    resp = await _peticion_alertas(sesion_de_pruebas)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_alertas_padre_200(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    resp = await _peticion_alertas(sesion_de_pruebas, 'padre', usuario_de_pruebas)
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_reportes_sin_permiso_padre_403(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    resp = await _peticion_reportes(sesion_de_pruebas, 'padre', usuario_de_pruebas)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_reportes_propietario_200(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    resp = await _peticion_reportes(sesion_de_pruebas, 'propietario', usuario_de_pruebas)
    assert resp.status_code == status.HTTP_200_OK

