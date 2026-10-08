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
    r = await sesion.execute(
        text('INSERT INTO categoria (nombre) VALUES (:nombre) RETURNING id'),
        {'nombre': nombre},
    )
    return r.scalar_one()


async def _crear_proveedor(sesion: AsyncSession, nombre: str) -> UUID:
    r = await sesion.execute(
        text('INSERT INTO proveedor (nombre) VALUES (:nombre) RETURNING id'),
        {'nombre': nombre},
    )
    return r.scalar_one()


async def _crear_producto(
    sesion: AsyncSession,
    categoria_id: UUID,
    proveedor_id: UUID,
    codigo: str,
    nombre: str,
    umbral_minimo: Decimal = Decimal('5.00'),
    dias_aviso: int = 30,
    fecha_venc: date | None = None,
) -> UUID:
    r = await sesion.execute(
        text(
            'INSERT INTO producto (codigo, nombre, categoria_id, proveedor_id, '
            'precio_venta, precio_costo, umbral_minimo, dias_vencimiento_aviso, '
            'fecha_vencimiento) VALUES (:codigo, :nombre, :categoria_id, :proveedor_id, '
            '10.00, 5.00, :umbral_minimo, :dias_aviso, :fecha_venc) RETURNING id'
        ),
        {
            'codigo': codigo,
            'nombre': nombre,
            'categoria_id': categoria_id,
            'proveedor_id': proveedor_id,
            'umbral_minimo': umbral_minimo,
            'dias_aviso': dias_aviso,
            'fecha_venc': fecha_venc,
        },
    )
    return r.scalar_one()


async def _generar_sugerencias(sesion: AsyncSession, rol: str, usuario_id: UUID):
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url='http://test'
        ) as ac:
            return await ac.post('/api/sugerencias/generar')
    finally:
        app.dependency_overrides.clear()


async def _listar_sugerencias(sesion: AsyncSession, rol: str, usuario_id: UUID, params=None):
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url='http://test'
        ) as ac:
            return await ac.get('/api/sugerencias', params=params)
    finally:
        app.dependency_overrides.clear()


async def _patch_sugerencia(sesion: AsyncSession, rol: str, usuario_id: UUID, sug_id: UUID, estado: str):
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url='http://test'
        ) as ac:
            return await ac.patch(f'/api/sugerencias/{sug_id}', json={'estado': estado})
    finally:
        app.dependency_overrides.clear()


async def _listar_notificaciones(sesion: AsyncSession, rol: str, usuario_id: UUID, params=None):
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url='http://test'
        ) as ac:
            return await ac.get('/api/notificaciones', params=params)
    finally:
        app.dependency_overrides.clear()


async def _marcar_notificacion_leida(sesion: AsyncSession, rol: str, usuario_id: UUID, nid: UUID):
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url='http://test'
        ) as ac:
            return await ac.patch(f'/api/notificaciones/{nid}/leida')
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_01_generar_con_ventas_recientes_y_stock_bajo_crea_sugerencia(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas
):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'C1')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P1')
    prod_id = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'P001', 'Prod1', umbral_minimo=Decimal('5.00'))
    hoy = date.today()
    for dias_atras in range(7):
        fecha_vta = hoy - timedelta(days=dias_atras)
        venta_id = (await sesion_de_pruebas.execute(
            text(
                "INSERT INTO venta (folio, cliente_id, usuario_id, fecha, subtotal, descuento, total, estado, metodo_pago) VALUES (:folio, :cli, :usr, :f, 20, 0, 20, 'activa', 'efectivo') RETURNING id"
            ),
            {'folio': f'F-2026-{1000 + dias_atras:04d}', 'cli': None, 'usr': usuario_de_pruebas, 'alm': almacen_de_pruebas, 'f': fecha_vta},
        )).scalar_one()
        await sesion_de_pruebas.execute(
            text(
                'INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (:v, :p, 2, 10, 20)'
            ),
            {'v': venta_id, 'p': prod_id},
        )
    await sesion_de_pruebas.execute(
        text('INSERT INTO existencia (almacen_id, producto_id, cantidad) SELECT id, :p, 1.00 FROM almacen WHERE nombre = :alm'),
        {'alm': almacen_de_pruebas, 'p': prod_id},
    )
    await sesion_de_pruebas.commit()
    resp = await _generar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    assert resp.status_code == 200
    data = resp.json()
    assert data['sugerencias_creadas'] == 1
    assert data['predicciones_creadas'] == 1
    lst = await _listar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    assert lst.status_code == 200
    items = lst.json()['items']
    assert len(items) == 1
    sug = items[0]
    assert sug['prioridad'] == 'alta'
    assert Decimal(sug['demanda_pronosticada']) == Decimal('14.00')
    assert Decimal(sug['stock_proyectado']) == Decimal('1.00')
    assert Decimal(sug['cantidad_sugerida']) == Decimal('18.00')

@pytest.mark.asyncio
async def test_02_generar_con_stock_sobra_no_crea_sugerencia(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas
):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'C2')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P2')
    prod_id = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'P002', 'Prod2', umbral_minimo=Decimal('5.00'))
    hoy = date.today()
    for dias_atras in range(7):
        fecha_vta = hoy - timedelta(days=dias_atras)
        venta_id = (await sesion_de_pruebas.execute(
            text(
                "INSERT INTO venta (folio, cliente_id, usuario_id, fecha, subtotal, descuento, total, estado, metodo_pago) VALUES (:folio, :cli, :usr, :f, 10, 0, 10, 'activa', 'efectivo') RETURNING id"
            ),
            {'folio': f'F-2026-{1000 + dias_atras:04d}', 'cli': None, 'usr': usuario_de_pruebas, 'alm': almacen_de_pruebas, 'f': fecha_vta},
        )).scalar_one()
        await sesion_de_pruebas.commit()
    await sesion_de_pruebas.execute(
        text('INSERT INTO existencia (almacen_id, producto_id, cantidad) SELECT id, :p, 20.00 FROM almacen WHERE nombre = :alm'),
        {'alm': almacen_de_pruebas, 'p': prod_id},
    )
    await sesion_de_pruebas.commit()
    resp = await _generar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    assert resp.status_code == 200
    assert resp.json()['sugerencias_creadas'] == 0

@pytest.mark.asyncio
async def test_03_generar_dos_veces_no_duplica_sugerencia_pendiente(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas
):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'C3')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P3')
    prod_id = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'P003', 'Prod3', umbral_minimo=Decimal('5.00'))
    hoy = date.today()
    for dias_atras in range(7):
        fecha_vta = hoy - timedelta(days=dias_atras)
        venta_id = (await sesion_de_pruebas.execute(
            text(
                "INSERT INTO venta (folio, cliente_id, usuario_id, fecha, subtotal, descuento, total, estado, metodo_pago) VALUES (:folio, :cli, :usr, :f, 20, 0, 20, 'activa', 'efectivo') RETURNING id"
            ),
            {'folio': f'F-2026-{1000 + dias_atras:04d}', 'cli': None, 'usr': usuario_de_pruebas, 'alm': almacen_de_pruebas, 'f': fecha_vta},
        )).scalar_one()
        await sesion_de_pruebas.execute(
            text(
                'INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (:v, :p, 2, 10, 20)'
            ),
            {'v': venta_id, 'p': prod_id},
        )
    await sesion_de_pruebas.execute(
        text('INSERT INTO existencia (almacen_id, producto_id, cantidad) SELECT id, :p, 1.00 FROM almacen WHERE nombre = :alm'),
        {'alm': almacen_de_pruebas, 'p': prod_id},
    )
    await sesion_de_pruebas.commit()
    r1 = await _generar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    assert r1.json()['sugerencias_creadas'] == 1
    r2 = await _generar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    assert r2.json()['sugerencias_creadas'] == 0

@pytest.mark.asyncio
async def test_04_permisos_generar(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas
):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'C4')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P4')
    await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'P004', 'Prod4')
    await sesion_de_pruebas.commit()
    r_prop = await _generar_sugerencias(sesion_de_pruebas, 'propietario', usuario_de_pruebas)
    assert r_prop.status_code == 403
    r_adm = await _generar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    assert r_adm.status_code == 200

@pytest.mark.asyncio
async def test_05_datos_ficticios_y_confianza(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas, monkeypatch
):
    from app.core import config

    cat_id = await _crear_categoria(sesion_de_pruebas, 'C5')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P5')
    prod_id = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'P005', 'Prod5', umbral_minimo=Decimal('5.00'))
    hoy = date.today()
    for dias_atras in range(7):
        fecha_vta = hoy - timedelta(days=dias_atras)
        venta_id = (await sesion_de_pruebas.execute(
            text(
                "INSERT INTO venta (folio, cliente_id, usuario_id, fecha, subtotal, descuento, total, estado, metodo_pago) VALUES (:folio, :cli, :usr, :f, 20, 0, 20, 'activa', 'efectivo') RETURNING id"
            ),
            {'folio': f'F-2026-{1000 + dias_atras:04d}', 'cli': None, 'usr': usuario_de_pruebas, 'alm': almacen_de_pruebas, 'f': fecha_vta},
        )).scalar_one()
        await sesion_de_pruebas.execute(
            text(
                'INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (:v, :p, 2, 10, 20)'
            ),
            {'v': venta_id, 'p': prod_id},
        )
    await sesion_de_pruebas.execute(
        text('INSERT INTO existencia (almacen_id, producto_id, cantidad) SELECT id, :p, 1.00 FROM almacen WHERE nombre = :alm'),
        {'alm': almacen_de_pruebas, 'p': prod_id},
    )
    await sesion_de_pruebas.commit()

    monkeypatch.setattr(config.settings, 'DATOS_FICTICIOS', True)
    resp = await _generar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    assert resp.status_code == 200
    pred = await sesion_de_pruebas.execute(text('SELECT nivel_confianza, datos_ficticios FROM prediccion WHERE datos_ficticios = true LIMIT 1'))
    pf = pred.mappings().first()
    assert pf['nivel_confianza'] == 'simulacion'
    assert pf['datos_ficticios'] is True

    monkeypatch.setattr(config.settings, 'DATOS_FICTICIOS', False)
    await _generar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)  # no duplica sugerencia, crea prediccion
    pred2 = await sesion_de_pruebas.execute(text('SELECT nivel_confianza, datos_ficticios FROM prediccion WHERE datos_ficticios = false LIMIT 1'))
    pf2 = pred2.mappings().first()
    assert pf2['nivel_confianza'] == 'baja'
    assert pf2['datos_ficticios'] is False

@pytest.mark.asyncio
async def test_06_patch_sugerencia(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas
):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'C6')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P6')
    prod_id = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'P006', 'Prod6', umbral_minimo=Decimal('5.00'))
    hoy = date.today()
    for dias_atras in range(7):
        fecha_vta = hoy - timedelta(days=dias_atras)
        venta_id = (await sesion_de_pruebas.execute(
            text(
                "INSERT INTO venta (folio, cliente_id, usuario_id, fecha, subtotal, descuento, total, estado, metodo_pago) VALUES (:folio, :cli, :usr, :f, 20, 0, 20, 'activa', 'efectivo') RETURNING id"
            ),
            {'folio': f'F-2026-{1000 + dias_atras:04d}', 'cli': None, 'usr': usuario_de_pruebas, 'alm': almacen_de_pruebas, 'f': fecha_vta},
        )).scalar_one()
        await sesion_de_pruebas.execute(
            text(
                'INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (:v, :p, 2, 10, 20)'
            ),
            {'v': venta_id, 'p': prod_id},
        )
    await sesion_de_pruebas.execute(
        text('INSERT INTO existencia (almacen_id, producto_id, cantidad) SELECT id, :p, 1.00 FROM almacen WHERE nombre = :alm'),
        {'alm': almacen_de_pruebas, 'p': prod_id},
    )
    await sesion_de_pruebas.commit()
    await _generar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    lst = await _listar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    sug_id = lst.json()['items'][0]['id']
    r = await _patch_sugerencia(sesion_de_pruebas, 'administrador', usuario_de_pruebas, UUID(sug_id), 'atendida')
    assert r.status_code == 200
    r2 = await _patch_sugerencia(sesion_de_pruebas, 'administrador', usuario_de_pruebas, UUID(sug_id), 'atendida')
    assert r2.status_code == 409
    r3 = await _patch_sugerencia(sesion_de_pruebas, 'administrador', usuario_de_pruebas, UUID(sug_id), 'invalida')
    assert r3.status_code == 422

@pytest.mark.asyncio
async def test_07_padre_permisos(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas
):
    cat_id = await _crear_categoria(sesion_de_pruebas, 'C7')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P7')
    await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'P007', 'Prod7')
    await sesion_de_pruebas.commit()
    gen = await _generar_sugerencias(sesion_de_pruebas, 'padre', usuario_de_pruebas)
    assert gen.status_code == 403

@pytest.mark.asyncio
async def test_08_notificaciones_usuario_y_generales(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas
):
    from conftest import simular_rol

    otro_auth = UUID('12345678-1234-5678-1234-567812345678')
    await sesion_de_pruebas.execute(
        text('INSERT INTO auth.users (id) VALUES (:aid)'),
        {'aid': otro_auth},
    )
    otro = await sesion_de_pruebas.execute(
        text(
            'INSERT INTO usuario (auth_id, nombre, email, rol, activo) '
            'VALUES (:aid, :n, :e, :r, true) RETURNING id'
        ),
        {'aid': otro_auth, 'n': 'Otro', 'e': 'otro@test.invalid', 'r': 'propietario'},
    )
    otro_id = otro.scalar_one()

    cat_id = await _crear_categoria(sesion_de_pruebas, 'C8')
    prov_id = await _crear_proveedor(sesion_de_pruebas, 'P8')
    prod_id = await _crear_producto(sesion_de_pruebas, cat_id, prov_id, 'P008', 'Prod8', umbral_minimo=Decimal('5.00'))
    hoy = date.today()
    for dias_atras in range(7):
        fecha_vta = hoy - timedelta(days=dias_atras)
        venta_id = (await sesion_de_pruebas.execute(
            text(
                "INSERT INTO venta (folio, cliente_id, usuario_id, fecha, subtotal, descuento, total, estado, metodo_pago) VALUES (:folio, :cli, :usr, :f, 20, 0, 20, 'activa', 'efectivo') RETURNING id"
            ),
            {'folio': f'F-2026-{1000 + dias_atras:04d}', 'cli': None, 'usr': usuario_de_pruebas, 'alm': almacen_de_pruebas, 'f': fecha_vta},
        )).scalar_one()
        await sesion_de_pruebas.execute(
            text(
                'INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (:v, :p, 2, 10, 20)'
            ),
            {'v': venta_id, 'p': prod_id},
        )
    await sesion_de_pruebas.execute(
        text('INSERT INTO existencia (almacen_id, producto_id, cantidad) SELECT id, :p, 1.00 FROM almacen WHERE nombre = :alm'),
        {'alm': almacen_de_pruebas, 'p': prod_id},
    )
    await sesion_de_pruebas.commit()
    await _generar_sugerencias(sesion_de_pruebas, 'administrador', usuario_de_pruebas)

    r_mio = await _listar_notificaciones(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    assert r_mio.status_code == 200
    items_mio = r_mio.json()['items']
    assert any(n['tipo'] == 'sugerencia_compra' for n in items_mio)

    r_otro = await _listar_notificaciones(sesion_de_pruebas, 'propietario', otro_id)
    assert r_otro.status_code == 200
    items_otro = r_otro.json()['items']
    assert any(n['tipo'] == 'sugerencia_compra' for n in items_otro)

    gen = items_mio if any(n['tipo'] == 'sugerencia_compra' for n in items_mio) else items_otro
    nid = next(n['id'] for n in (items_mio + items_otro) if n['tipo'] == 'sugerencia_compra')
    r_leer = await _marcar_notificacion_leida(sesion_de_pruebas, 'administrador', usuario_de_pruebas, UUID(nid))
    assert r_leer.status_code == 200















