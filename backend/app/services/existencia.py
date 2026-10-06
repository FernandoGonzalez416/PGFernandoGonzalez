from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errores import StockInsuficienteError
from app.schemas.existencia import ExistenciaAjuste, ExistenciaRead
from app.schemas.inventario import MovimientoRead
from app.services.productos import obtener_almacen_por_defecto, obtener_producto

SELECCION_EXISTENCIA = """
    SELECT e.producto_id, e.almacen_id, a.nombre AS almacen_nombre,
           e.cantidad, e.updated_at
    FROM existencia e
    JOIN almacen a ON a.id = e.almacen_id
"""

SELECCION_MOVIMIENTO = """
    SELECT m.id, m.producto_id, m.almacen_id, m.tipo, m.referencia_tipo,
           m.referencia_id, m.cantidad, m.usuario_id, m.nota, m.fecha
    FROM movimiento_inventario m
"""


async def ajustar_existencia(
    sesion: AsyncSession, datos: ExistenciaAjuste, usuario_id: UUID
) -> ExistenciaRead:
    """Aplica un delta firmado al stock y deja el movimiento que lo justifica.

    Dos garantías en una sola transacción: la existencia nunca queda en
    negativo y nunca se toca sin dejar `movimiento_inventario`.
    """
    producto = await obtener_producto(sesion, datos.producto_id)
    almacen_id = await obtener_almacen_por_defecto(sesion)
    autor = UUID(str(usuario_id))
    delta = datos.cantidad

    async with sesion.begin_nested():
        actual = (
            await sesion.execute(
                text(
                    """
                    SELECT cantidad FROM existencia
                    WHERE producto_id = :producto_id AND almacen_id = :almacen_id
                    FOR UPDATE
                    """
                ),
                {"producto_id": producto.id, "almacen_id": almacen_id},
            )
        ).scalar_one_or_none()
        disponible = actual if actual is not None else Decimal("0.00")
        resultado = disponible + delta

        if resultado < 0:
            raise StockInsuficienteError(
                f"El ajuste dejaría el stock de '{producto.nombre}' en {resultado}; "
                f"solo hay {disponible} disponibles"
            )

        await sesion.execute(
            text(
                """
                INSERT INTO existencia (producto_id, almacen_id, cantidad)
                VALUES (:producto_id, :almacen_id, :cantidad)
                ON CONFLICT (producto_id, almacen_id) DO UPDATE
                SET cantidad = EXCLUDED.cantidad
                """
            ),
            {
                "producto_id": producto.id,
                "almacen_id": almacen_id,
                "cantidad": resultado,
            },
        )
        await sesion.execute(
            text(
                """
                INSERT INTO movimiento_inventario (
                    producto_id, almacen_id, tipo, referencia_tipo,
                    cantidad, usuario_id, nota
                )
                VALUES (
                    :producto_id, :almacen_id, :tipo, 'ajuste',
                    :cantidad, :usuario_id, :nota
                )
                """
            ),
            {
                "producto_id": producto.id,
                "almacen_id": almacen_id,
                "tipo": "entrada" if delta > 0 else "salida",
                "cantidad": abs(delta),
                "usuario_id": autor,
                "nota": datos.nota,
            },
        )

    return await _leer_existencia(sesion, producto.id, almacen_id)


async def _leer_existencia(
    sesion: AsyncSession, producto_id: UUID, almacen_id: UUID
) -> ExistenciaRead:
    """Lee la existencia recién escrita; el `upsert` garantiza que existe."""
    fila = (
        await sesion.execute(
            text(
                f"{SELECCION_EXISTENCIA} "
                "WHERE e.producto_id = :producto_id AND e.almacen_id = :almacen_id"
            ),
            {"producto_id": producto_id, "almacen_id": almacen_id},
        )
    ).mappings().one()
    return ExistenciaRead(**dict(fila))


async def listar_existencias(
    sesion: AsyncSession, producto_id: UUID | None = None
) -> list[ExistenciaRead]:
    condiciones = ""
    parametros: dict[str, object] = {}
    if producto_id is not None:
        condiciones = "WHERE e.producto_id = :producto_id"
        parametros["producto_id"] = producto_id

    filas = (
        await sesion.execute(
            text(
                f"{SELECCION_EXISTENCIA} {condiciones} "
                "ORDER BY a.nombre, e.producto_id"
            ),
            parametros,
        )
    ).mappings().all()
    return [ExistenciaRead(**dict(fila)) for fila in filas]


async def listar_movimientos(
    sesion: AsyncSession,
    producto_id: UUID | None = None,
    limite: int = 50,
    desplazamiento: int = 0,
) -> list[MovimientoRead]:
    condiciones = ""
    parametros: dict[str, object] = {
        "limite": limite,
        "desplazamiento": desplazamiento,
    }
    if producto_id is not None:
        condiciones = "WHERE m.producto_id = :producto_id"
        parametros["producto_id"] = producto_id

    filas = (
        await sesion.execute(
            text(
                f"{SELECCION_MOVIMIENTO} {condiciones} "
                "ORDER BY m.fecha DESC, m.id DESC "
                "LIMIT :limite OFFSET :desplazamiento"
            ),
            parametros,
        )
    ).mappings().all()
    return [MovimientoRead(**dict(fila)) for fila in filas]
