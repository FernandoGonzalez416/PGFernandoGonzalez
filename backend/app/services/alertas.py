from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def obtener_bajo_stock(db: AsyncSession) -> list[dict]:
    hoy = date.today()
    query = text(
        """
        SELECT p.id AS producto_id, p.codigo, p.nombre, p.umbral_minimo,
               COALESCE(SUM(e.cantidad), 0)::numeric(12,2) AS existencia_total
        FROM producto p
        LEFT JOIN existencia e ON e.producto_id = p.id
        WHERE p.activo = true
        GROUP BY p.id, p.codigo, p.nombre, p.umbral_minimo
        HAVING COALESCE(SUM(e.cantidad), 0) <= p.umbral_minimo
        ORDER BY p.nombre
        """
    )
    resultado = await db.execute(query)
    filas = resultado.fetchall()
    return [
        {
            "producto_id": fila.producto_id,
            "codigo": fila.codigo,
            "nombre": fila.nombre,
            "existencia": fila.existencia_total,
            "umbral_minimo": fila.umbral_minimo,
            "almacen_id": None,
            "agotado": float(fila.existencia_total) == 0.0,
        }
        for fila in filas
    ]


async def obtener_vencimiento_proximo(db: AsyncSession) -> list[dict]:
    hoy = date.today()
    query = text(
        """
        SELECT p.id AS producto_id, p.codigo, p.nombre, p.fecha_vencimiento,
               p.dias_vencimiento_aviso
        FROM producto p
        WHERE p.activo = true
        AND p.fecha_vencimiento IS NOT NULL
        AND p.fecha_vencimiento <= current_date + p.dias_vencimiento_aviso
        ORDER BY p.fecha_vencimiento
        """
    )
    resultado = await db.execute(query)
    filas = resultado.fetchall()
    alertas: list[dict] = []
    for fila in filas:
        dias_restantes = None
        if fila.fecha_vencimiento is not None:
            dias_restantes = (fila.fecha_vencimiento - hoy).days
        alertas.append(
            {
                "producto_id": fila.producto_id,
                "codigo": fila.codigo,
                "nombre": fila.nombre,
                "fecha_vencimiento": fila.fecha_vencimiento,
                "dias_vencimiento_aviso": fila.dias_vencimiento_aviso,
                "dias_restantes": dias_restantes,
                "almacen_id": None,
                "vencido": dias_restantes is not None and dias_restantes < 0,
            }
        )
    return alertas


async def obtener_resumen_alertas(db: AsyncSession) -> dict:
    bajo_stock = await obtener_bajo_stock(db)
    vencimiento_proximo = await obtener_vencimiento_proximo(db)
    return {
        "bajo_stock": bajo_stock,
        "vencimiento_proximo": vencimiento_proximo,
    }
