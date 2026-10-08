from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def obtener_productos_mas_vendidos(
    db: AsyncSession,
    fecha_inicio: date,
    fecha_fin: date,
    limite: int = 10,
) -> list[dict]:
    query = text(
        """
        SELECT p.id AS producto_id, p.codigo, p.nombre,
               SUM(dv.cantidad)::numeric(12,2) AS cantidad_vendida,
               SUM(dv.subtotal)::numeric(12,2) AS total_vendido
        FROM producto p
        JOIN detalle_venta dv ON dv.producto_id = p.id
        JOIN venta v ON v.id = dv.venta_id
        WHERE v.estado = 'activa'
          AND v.fecha >= :fini
          AND v.fecha < :ffin
        GROUP BY p.id, p.codigo, p.nombre
        ORDER BY SUM(dv.cantidad) DESC, p.nombre ASC
        LIMIT :lim
        """
    )
    resultado = await db.execute(
        query,
        {
            "fini": datetime.combine(fecha_inicio, datetime.min.time()),
            "ffin": datetime.combine(fecha_fin + timedelta(days=1), datetime.min.time()),
            "lim": limite,
        },
    )
    filas = resultado.fetchall()
    return [
        {
            "producto_id": fila.producto_id,
            "codigo": fila.codigo,
            "nombre": fila.nombre,
            "cantidad_vendida": fila.cantidad_vendida,
            "total_vendido": fila.total_vendido,
        }
        for fila in filas
    ]
