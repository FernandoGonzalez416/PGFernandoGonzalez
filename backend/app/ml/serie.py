"""Serie diaria por producto: unidades vendidas por día desde la primera venta hasta AYER."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List
from uuid import UUID

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def obtener_serie_diaria(
    sesion: AsyncSession,
    producto_id: UUID,
) -> Dict[str, object]:
    """
    Obtiene la serie diaria de ventas para un producto.

    Retorna:
    - 'fechas': lista de date desde la primera venta hasta AYER (inclusive)
    - 'unidades': lista de int con unidades vendidas por día (0 si no hubo venta)
    - 'primera_venta': date de la primera venta (o None si no hay ventas)
    """
    hoy = date.today()
    ayer = hoy - timedelta(days=1)

    # Obtener primera venta del producto (solo ventas activas)
    primera_fila = await sesion.execute(
        text(
            """
            SELECT MIN((v.fecha AT TIME ZONE 'America/Guatemala')::date) AS primera
            FROM venta v
            JOIN detalle_venta dv ON dv.venta_id = v.id
            WHERE dv.producto_id = :pid AND v.estado = 'activa'
            """
        ),
        {"pid": producto_id},
    )
    primera_venta = primera_fila.scalar_one_or_none()

    if primera_venta is None:
        return {"fechas": [], "unidades": [], "primera_venta": None}

    # Generar todas las fechas desde primera_venta hasta ayer
    dias_totales = (ayer - primera_venta).days + 1
    fechas = [primera_venta + timedelta(days=i) for i in range(dias_totales)]

    # Obtener ventas agregadas por día
    filas = await sesion.execute(
        text(
            """
            SELECT (v.fecha AT TIME ZONE 'America/Guatemala')::date AS dia,
                   COALESCE(SUM(dv.cantidad), 0) AS unidades
            FROM venta v
            JOIN detalle_venta dv ON dv.venta_id = v.id
            WHERE dv.producto_id = :pid
              AND v.estado = 'activa'
              AND (v.fecha AT TIME ZONE 'America/Guatemala')::date BETWEEN :ini AND :fin
            GROUP BY 1
            ORDER BY 1
            """
        ),
        {"pid": producto_id, "ini": primera_venta, "fin": ayer},
    )

    ventas_por_dia = {fila["dia"]: int(fila["unidades"]) for fila in filas.mappings()}

    # Construir serie completa con ceros en días sin venta
    unidades = [ventas_por_dia.get(f, 0) for f in fechas]

    return {
        "fechas": fechas,
        "unidades": unidades,
        "primera_venta": primera_venta,
    }


def serie_a_array(unidades: List[int]) -> np.ndarray:
    """Convierte lista de unidades a array numpy float64."""
    return np.array(unidades, dtype=np.float64)