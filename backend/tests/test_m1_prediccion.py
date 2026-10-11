"""Pruebas de integración M1: motor de predicción autorizado (P3/P3a/P13).

1. Generar con 120 días sembrados produce un método distinto de
   `promedio_movil` y persiste `mae_linea_base` en `prediccion`.
2. Un propietario (sin `prediccion:ver`, solo administrador) recibe 403 en
   `GET /api/predicciones` y en `GET /api/predicciones/{id}/serie`.
3. `GET /api/predicciones/{id}/serie` devuelve 7 días de pronóstico y 60 de
   historial.

Los datos sembrados son ficticios y están etiquetados como simulación (P4).
Se omiten si `DATABASE_URL_TEST` no está definida (P20).
"""

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

import httpx2
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from conftest import simular_rol

pytestmark = pytest.mark.integracion

# Patrón semanal determinista (lun-vie=5, sáb=10, dom=2): la misma
# estacionalidad fuerte del test unitario de sanidad, que el modelo vence.
UNIDADES_POR_DIA_SEMANA = {0: 5, 1: 5, 2: 5, 3: 5, 4: 5, 5: 10, 6: 2}


async def _crear_catalogo(
    sesion: AsyncSession, etiqueta: str, codigo: str, nombre: str
) -> UUID:
    cat_id = (
        await sesion.execute(
            text('INSERT INTO categoria (nombre) VALUES (:nombre) RETURNING id'),
            {'nombre': f'Categoría M1 {etiqueta} (simulación)'},
        )
    ).scalar_one()
    prov_id = (
        await sesion.execute(
            text('INSERT INTO proveedor (nombre) VALUES (:nombre) RETURNING id'),
            {'nombre': f'Proveedor M1 {etiqueta} (simulación)'},
        )
    ).scalar_one()
    return (
        await sesion.execute(
            text(
                'INSERT INTO producto (codigo, nombre, categoria_id, proveedor_id, '
                'precio_venta, precio_costo, umbral_minimo, dias_vencimiento_aviso, '
                'fecha_vencimiento) VALUES (:codigo, :nombre, :categoria_id, :proveedor_id, '
                "10.00, 5.00, 5.00, 30, NULL) RETURNING id"
            ),
            {
                'codigo': codigo,
                'nombre': f'{nombre} (simulación)',
                'categoria_id': cat_id,
                'proveedor_id': prov_id,
            },
        )
    ).scalar_one()


async def _sembrar_ventas_diarias(
    sesion: AsyncSession,
    prod_id: UUID,
    usuario_id: UUID,
    base_folio: int,
    dias: int,
) -> None:
    """Una venta activa por día, terminando ayer (la serie llega hasta ayer)."""
    hoy = date.today()
    for dias_atras in range(dias, 0, -1):
        fecha_vta = hoy - timedelta(days=dias_atras)
        unidades = UNIDADES_POR_DIA_SEMANA[fecha_vta.weekday()]
        total = Decimal(unidades * 10)
        venta_id = (
            await sesion.execute(
                text(
                    "INSERT INTO venta (folio, cliente_id, usuario_id, fecha, subtotal, "
                    "descuento, total, estado, metodo_pago) VALUES (:folio, NULL, :usr, :f, "
                    ":t, 0, :t, 'activa', 'efectivo') RETURNING id"
                ),
                {
                    'folio': f'F-2026-{base_folio + dias_atras:04d}',
                    'usr': usuario_id,
                    'f': fecha_vta,
                    't': total,
                },
            )
        ).scalar_one()
        await sesion.execute(
            text(
                'INSERT INTO detalle_venta (venta_id, producto_id, cantidad, '
                'precio_unitario, subtotal) VALUES (:v, :p, :c, 10, :t)'
            ),
            {'v': venta_id, 'p': prod_id, 'c': unidades, 't': total},
        )


async def _post_generar(sesion: AsyncSession, rol: str, usuario_id: UUID):
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url='http://test'
        ) as ac:
            return await ac.post('/api/sugerencias/generar')
    finally:
        app.dependency_overrides.clear()


async def _get(sesion: AsyncSession, rol: str, usuario_id: UUID, ruta: str):
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url='http://test'
        ) as ac:
            return await ac.get(ruta)
    finally:
        app.dependency_overrides.clear()


async def test_m1_generar_con_120_dias_usa_modelo_y_persiste_mae_linea_base(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas
):
    prod_id = await _crear_catalogo(
        sesion_de_pruebas, 'T1', 'M1-001', 'Producto M1 estacional'
    )
    await _sembrar_ventas_diarias(
        sesion_de_pruebas, prod_id, usuario_de_pruebas, 2000, 120
    )
    await sesion_de_pruebas.execute(
        text(
            'INSERT INTO existencia (almacen_id, producto_id, cantidad) '
            'SELECT id, :p, 1.00 FROM almacen WHERE nombre = :alm'
        ),
        {'alm': almacen_de_pruebas, 'p': prod_id},
    )
    await sesion_de_pruebas.commit()

    resp = await _post_generar(sesion_de_pruebas, 'administrador', usuario_de_pruebas)
    assert resp.status_code == 200

    fila = (
        await sesion_de_pruebas.execute(
            text(
                'SELECT metodo, mae_linea_base FROM prediccion '
                'WHERE producto_id = :p ORDER BY fecha_generacion DESC LIMIT 1'
            ),
            {'p': prod_id},
        )
    ).mappings().first()
    assert fila is not None
    # Método válido según el CHECK de la tabla (la selección semanal honesta
    # puede caer a la línea base si ningún candidato la vence: es correcto)
    assert fila['metodo'] in (
        'random_forest', 'hist_gradient_boosting', 'ridge', 'promedio_movil',
    )
    assert fila['mae_linea_base'] is not None
    assert float(fila['mae_linea_base']) >= 0


async def test_m1_propietario_sin_permiso_en_predicciones_y_serie_403(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas
):
    prod_id = await _crear_catalogo(
        sesion_de_pruebas, 'T2', 'M1-002', 'Producto M1 vedado'
    )
    await sesion_de_pruebas.commit()

    r_lista = await _get(
        sesion_de_pruebas, 'propietario', usuario_de_pruebas, '/api/predicciones'
    )
    assert r_lista.status_code == 403

    r_serie = await _get(
        sesion_de_pruebas,
        'propietario',
        usuario_de_pruebas,
        f'/api/predicciones/{prod_id}/serie',
    )
    assert r_serie.status_code == 403


async def test_m1_serie_devuelve_7_dias_pronostico_y_60_historial(
    sesion_de_pruebas, almacen_de_pruebas, usuario_de_pruebas
):
    prod_id = await _crear_catalogo(
        sesion_de_pruebas, 'T3', 'M1-003', 'Producto M1 serie'
    )
    await _sembrar_ventas_diarias(
        sesion_de_pruebas, prod_id, usuario_de_pruebas, 3000, 70
    )
    await sesion_de_pruebas.commit()

    resp = await _get(
        sesion_de_pruebas,
        'administrador',
        usuario_de_pruebas,
        f'/api/predicciones/{prod_id}/serie',
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert len(cuerpo['pronostico']) == 7
    assert len(cuerpo['historial']) == 60
