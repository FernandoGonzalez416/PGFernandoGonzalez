import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

import httpx2
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from conftest import simular_rol

pytestmark = pytest.mark.integracion

async def _crear_categoria(sesion: AsyncSession, nombre: str) -> UUID:
    r = await sesion.execute(text('INSERT INTO categoria (nombre) VALUES (:nombre) RETURNING id'), {'nombre': nombre})
    return r.scalar_one()
async def _crear_proveedor(sesion: AsyncSession, nombre: str) -> UUID:
    r = await sesion.execute(text('INSERT INTO proveedor (nombre) VALUES (:nombre) RETURNING id'), {'nombre': nombre})
    return r.scalar_one()
async def _crear_producto(sesion: AsyncSession, categoria_id: UUID, proveedor_id: UUID, codigo: str, nombre: str, umbral_minimo: Decimal = Decimal('5.00'), dias_aviso: int = 30, fecha_venc: date | None = None) -> UUID:
    r = await sesion.execute(text('INSERT INTO producto (codigo, nombre, categoria_id, proveedor_id, precio_venta, precio_costo, umbral_minimo, dias_vencimiento_aviso, fecha_vencimiento) VALUES (:codigo, :nombre, :categoria_id, :proveedor_id, 10.00, 5.00, :umbral_minimo, :dias_aviso, :fecha_venc) RETURNING id'), {'codigo': codigo, 'nombre': nombre, 'categoria_id': categoria_id, 'proveedor_id': proveedor_id, 'umbral_minimo': umbral_minimo, 'dias_aviso': dias_aviso, 'fecha_venc': fecha_venc})
    return r.scalar_one()
async def _post_venta(sesion: AsyncSession, rol: str, usuario_id: UUID, lineas: list[dict], descuento: Decimal | str = '0.00'):
    simular_rol(sesion, rol, usuario_id)
    cuerpo = {'lineas': lineas, 'descuento': str(descuento), 'metodo_pago': 'efectivo'}
    try:
        async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url='http://test') as ac:
            return await ac.post('/api/ventas', json=cuerpo)
    finally:
        app.dependency_overrides.clear()

async def _anular_venta(sesion: AsyncSession, rol: str, usuario_id: UUID, venta_id: UUID, motivo: str):
    simular_rol(sesion, rol, usuario_id)
    cuerpo = {'motivo_anulacion': motivo}
    try:
        async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url='http://test') as ac:
            return await ac.post(f'/api/ventas/{venta_id}/anular', json=cuerpo)
    finally:
        app.dependency_overrides.clear()

async def _get_alertas(sesion: AsyncSession, rol: str, usuario_id: UUID):
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url='http://test') as ac:
            return await ac.get('/api/alertas/')
    finally:
        app.dependency_overrides.clear()

async def _get_reportes(sesion: AsyncSession, rol: str, usuario_id: UUID, params: dict | None = None):
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url='http://test') as ac:
            return await ac.get('/api/reportes/productos-mas-vendidos', params=params)
    finally:
        app.dependency_overrides.clear()
@pytest.mark.asyncio
async def test_bajo_stock_existe(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'C1')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P1')
    prod = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'B1', 'ProdBajo', umbral_minimo=Decimal('5.00'))
    alm_id = (await sesion_de_pruebas.execute(text('SELECT id FROM almacen LIMIT 1'))).scalar_one()
    await sesion_de_pruebas.execute(text('INSERT INTO existencia (producto_id, almacen_id, cantidad) VALUES (:p,:a,3)'), {'p': prod, 'a': alm_id})
    resp = await _get_alertas(sesion_de_pruebas, 'padre', usuario_de_pruebas)
    assert resp.status_code == 200
    ids = [b['producto_id'] for b in resp.json()['bajo_stock']]
    assert str(prod) in ids
@pytest.mark.asyncio
async def test_bajo_stock_agotado(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'C2')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P2')
    prod = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'B2', 'Agotado', umbral_minimo=Decimal('5.00'))
    alm_id = (await sesion_de_pruebas.execute(text('SELECT id FROM almacen LIMIT 1'))).scalar_one()
    await sesion_de_pruebas.execute(text('INSERT INTO existencia (producto_id, almacen_id, cantidad) VALUES (:p,:a,0)'), {'p': prod, 'a': alm_id})
    resp = await _get_alertas(sesion_de_pruebas, 'padre', usuario_de_pruebas)
    assert resp.status_code == 200
    bs = [b for b in resp.json()['bajo_stock'] if b['producto_id'] == str(prod)][0]
    assert bs['agotado'] is True


@pytest.mark.asyncio
async def test_bajo_stock_no_debe_aparecer(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'C3')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P3')
    prod = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'B3', 'Ok', umbral_minimo=Decimal('5.00'))
    alm_id = (await sesion_de_pruebas.execute(text('SELECT id FROM almacen LIMIT 1'))).scalar_one()
    await sesion_de_pruebas.execute(text('INSERT INTO existencia (producto_id, almacen_id, cantidad) VALUES (:p,:a,10)'), {'p': prod, 'a': alm_id})
    resp = await _get_alertas(sesion_de_pruebas, 'padre', usuario_de_pruebas)
    assert resp.status_code == 200
    ids = [b['producto_id'] for b in resp.json()['bajo_stock']]
    assert str(prod) not in ids
@pytest.mark.asyncio
async def test_vencimiento_aparece_proximo(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'CV1')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'PV1')
    prod = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'V1', 'VenProx', dias_aviso=30, fecha_venc=date.today()+timedelta(days=10))
    resp = await _get_alertas(sesion_de_pruebas, 'padre', usuario_de_pruebas)
    assert resp.status_code == 200
    items = [v for v in resp.json()['vencimiento_proximo'] if v['producto_id'] == str(prod)]
    assert items
    assert items[0]['dias_restantes'] == 10
    assert items[0]['vencido'] is False


@pytest.mark.asyncio
async def test_vencimiento_aparece_vencido(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'CV2')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'PV2')
    prod = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'V2', 'Vencido', dias_aviso=30, fecha_venc=date.today()-timedelta(days=1))
    resp = await _get_alertas(sesion_de_pruebas, 'padre', usuario_de_pruebas)
    assert resp.status_code == 200
    items = [v for v in resp.json()['vencimiento_proximo'] if v['producto_id'] == str(prod)]
    assert items
    assert items[0]['dias_restantes'] == -1
    assert items[0]['vencido'] is True


@pytest.mark.asyncio
async def test_vencimiento_no_aparece(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'CV3')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'PV3')
    prod = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'V3', 'Largo', dias_aviso=30, fecha_venc=date.today()+timedelta(days=90))
    resp = await _get_alertas(sesion_de_pruebas, 'padre', usuario_de_pruebas)
    assert resp.status_code == 200
    items = [v for v in resp.json()['vencimiento_proximo'] if v['producto_id'] == str(prod)]
    assert not items
@pytest.mark.asyncio
async def test_mas_vendidos_excluye_anuladas(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'CR1')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'PR1')
    p1 = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'R1', 'ProdA')
    p2 = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'R2', 'ProdB')
    alm_id = (await sesion_de_pruebas.execute(text('SELECT id FROM almacen LIMIT 1'))).scalar_one()
    await sesion_de_pruebas.execute(text('INSERT INTO existencia (producto_id, almacen_id, cantidad) VALUES (:p,:a,100)'), {'p': p1, 'a': alm_id})
    await sesion_de_pruebas.execute(text('INSERT INTO existencia (producto_id, almacen_id, cantidad) VALUES (:p,:a,100)'), {'p': p2, 'a': alm_id})
    resp1 = await _post_venta(sesion_de_pruebas, 'propietario', usuario_de_pruebas, lineas=[{'producto_id': str(p1), 'cantidad': 5}])
    assert resp1.status_code in (200,201)
    resp2 = await _post_venta(sesion_de_pruebas, 'propietario', usuario_de_pruebas, lineas=[{'producto_id': str(p2), 'cantidad': 2}])
    assert resp2.status_code in (200,201)
    resp3 = await _post_venta(sesion_de_pruebas, 'propietario', usuario_de_pruebas, lineas=[{'producto_id': str(p2), 'cantidad': 3}])
    assert resp3.status_code in (200,201)
    data3 = resp3.json()
    venta_id_anulada = data3.get('id') or data3.get('venta_id')
    await _anular_venta(sesion_de_pruebas, 'propietario', usuario_de_pruebas, venta_id_anulada, 'test')
    resp_r = await _get_reportes(sesion_de_pruebas, 'propietario', usuario_de_pruebas)
    assert resp_r.status_code == 200
    resultados = resp_r.json()
    assert resultados[0]['producto_id'] == str(p1)
    assert str(resultados[0]['cantidad_vendida']) == '5.00'
    assert str(Decimal(resultados[0]['total_vendido'])) == '50.00'
    assert resultados[1]['producto_id'] == str(p2)
    assert str(resultados[1]['cantidad_vendida']) == '2.00'
    assert str(Decimal(resultados[1]['total_vendido'])) == '20.00'


@pytest.mark.asyncio
async def test_mas_vendidos_fecha_invertida_422(sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas):
    params = {'fecha_inicio': (date.today()).isoformat(), 'fecha_fin': (date.today()-timedelta(days=1)).isoformat()}
    resp = await _get_reportes(sesion_de_pruebas, 'propietario', usuario_de_pruebas, params=params)
    assert resp.status_code == 422

