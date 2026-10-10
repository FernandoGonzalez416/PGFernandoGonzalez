from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capacidades import verificar_anulacion_venta
from app.core.dinero import a_cuantia
from app.core.errores import (
    AnulacionNoPermitidaError,
    ClienteInvalidoError,
    DescuentoInvalidoError,
    StockInsuficienteError,
    VentaNoAnulableError,
    VentaNoEncontradaError,
)
from app.schemas.venta import (
    AnulacionCreate,
    ResumenVentaDia,
    ResumenVentas,
    VentaCreate,
    VentaDetalleRead,
    VentaRead,
)
from app.services.folio import generar_folio
from app.services.productos import obtener_almacen_por_defecto, obtener_producto

SELECCION_VENTA = """
    SELECT v.id, v.folio, v.fecha, v.cliente_id, v.usuario_id,
           v.metodo_pago, v.subtotal, v.descuento, v.total, v.estado,
           v.motivo_anulacion
    FROM venta v
"""


async def _leer_lineas(sesion: AsyncSession, venta_id: UUID) -> list[VentaDetalleRead]:
    filas = (
        await sesion.execute(
            text(
                """
                SELECT dv.producto_id, p.nombre AS producto_nombre,
                       dv.cantidad, dv.precio_unitario, dv.subtotal
                FROM detalle_venta dv
                JOIN producto p ON p.id = dv.producto_id
                WHERE dv.venta_id = :venta_id
                ORDER BY dv.id
                """
            ),
            {"venta_id": venta_id},
        )
    ).mappings().all()
    return [VentaDetalleRead(**dict(fila)) for fila in filas]


async def _leer_venta(sesion: AsyncSession, venta_id: UUID) -> VentaRead:
    fila = (
        await sesion.execute(
            text(f"{SELECCION_VENTA} WHERE v.id = :venta_id"),
            {"venta_id": venta_id},
        )
    ).mappings().one_or_none()
    if fila is None:
        raise VentaNoEncontradaError(str(venta_id))
    return VentaRead(**dict(fila), lineas=await _leer_lineas(sesion, venta_id))


async def obtener_venta(sesion: AsyncSession, venta_id: UUID) -> VentaRead:
    return await _leer_venta(sesion, venta_id)


async def registrar_venta(
    sesion: AsyncSession, datos: VentaCreate, usuario_id: UUID
) -> VentaRead:
    """Registra una venta de forma atómica (plan, reglas 1-7).

    Ventas, detalles y movimientos se escriben en un único SAVEPOINT (P24):
    si algún producto falla la validación de stock, no queda ni venta ni
    movimiento parcial.
    """
    autor = UUID(str(usuario_id))
    almacen_id = await obtener_almacen_por_defecto(sesion)

    if datos.cliente_id is not None:
        existe_cliente = (
            await sesion.execute(
                text("SELECT 1 FROM cliente WHERE id = :cliente_id AND activo = TRUE"),
                {"cliente_id": datos.cliente_id},
            )
        ).scalar_one_or_none()
        if existe_cliente is None:
            raise ClienteInvalidoError("El cliente no existe o está inactivo")

    descuento = datos.descuento

    async with sesion.begin_nested():
        fusionadas: dict[UUID, int] = {}
        for linea in datos.lineas:
            fusionadas[linea.producto_id] = fusionadas.get(linea.producto_id, 0) + linea.cantidad

        lineas_resueltas: list[tuple[UUID, str, int, Decimal, Decimal]] = []
        subtotal = Decimal("0.00")
        for producto_id, cantidad in fusionadas.items():
            producto = await obtener_producto(sesion, producto_id)
            disponible = (
                await sesion.execute(
                    text(
                        """
                        SELECT cantidad FROM existencia
                        WHERE producto_id = :producto_id AND almacen_id = :almacen_id
                        FOR UPDATE
                        """
                    ),
                    {"producto_id": producto_id, "almacen_id": almacen_id},
                )
            ).scalar_one_or_none()
            disponible = disponible if disponible is not None else Decimal("0.00")
            if disponible < cantidad:
                raise StockInsuficienteError(
                    f"Stock insuficiente de '{producto.nombre}': se pidieron "
                    f"{cantidad} y solo hay {disponible}"
                )
            precio = a_cuantia(producto.precio_venta)
            subtotal_linea = cantidad * precio
            subtotal += subtotal_linea
            lineas_resueltas.append(
                (producto_id, producto.nombre, cantidad, precio, subtotal_linea)
            )

        subtotal = a_cuantia(subtotal)
        if descuento > subtotal:
            raise DescuentoInvalidoError(
                f"El descuento {descuento} supera el subtotal {subtotal}"
            )
        total = a_cuantia(subtotal - descuento)

        folio = await generar_folio(sesion)

        venta_id = (
            await sesion.execute(
                text(
                    """
                    INSERT INTO venta (
                        folio, cliente_id, usuario_id, metodo_pago,
                        subtotal, descuento, total
                    )
                    VALUES (
                        :folio, :cliente_id, :usuario_id, :metodo_pago,
                        :subtotal, :descuento, :total
                    )
                    RETURNING id
                    """
                ),
                {
                    "folio": folio,
                    "cliente_id": datos.cliente_id,
                    "usuario_id": autor,
                    "metodo_pago": datos.metodo_pago,
                    "subtotal": subtotal,
                    "descuento": descuento,
                    "total": total,
                },
            )
        ).scalar_one()

        for producto_id, _nombre, cantidad, precio, subtotal_linea in lineas_resueltas:
            await sesion.execute(
                text(
                    """
                    INSERT INTO detalle_venta (
                        venta_id, producto_id, cantidad, precio_unitario, subtotal
                    )
                    VALUES (
                        :venta_id, :producto_id, :cantidad, :precio_unitario, :subtotal
                    )
                    """
                ),
                {
                    "venta_id": venta_id,
                    "producto_id": producto_id,
                    "cantidad": cantidad,
                    "precio_unitario": precio,
                    "subtotal": subtotal_linea,
                },
            )
            await sesion.execute(
                text(
                    """
                    INSERT INTO movimiento_inventario (
                        producto_id, almacen_id, tipo, referencia_tipo,
                        referencia_id, cantidad, usuario_id, nota
                    )
                    VALUES (
                        :producto_id, :almacen_id, 'salida', 'venta',
                        :referencia_id, :cantidad, :usuario_id, :nota
                    )
                    """
                ),
                {
                    "producto_id": producto_id,
                    "almacen_id": almacen_id,
                    "referencia_id": venta_id,
                    "cantidad": cantidad,
                    "usuario_id": autor,
                    "nota": f"Venta {folio}",
                },
            )
            await sesion.execute(
                text(
                    """
                    UPDATE existencia
                    SET cantidad = cantidad - :cantidad
                    WHERE producto_id = :producto_id AND almacen_id = :almacen_id
                    """
                ),
                {
                    "producto_id": producto_id,
                    "almacen_id": almacen_id,
                    "cantidad": cantidad,
                },
            )

    return await _leer_venta(sesion, venta_id)


async def _obtener_venta(sesion: AsyncSession, venta_id: UUID) -> dict:
    fila = (
        await sesion.execute(
            text(f"{SELECCION_VENTA} WHERE v.id = :venta_id"),
            {"venta_id": venta_id},
        )
    ).mappings().one_or_none()
    if fila is None:
        raise VentaNoEncontradaError(str(venta_id))
    return dict(fila)


async def anular_venta(
    sesion: AsyncSession,
    venta_id: UUID,
    usuario_id: UUID,
    rol: str,
    datos: AnulacionCreate,
) -> VentaRead:
    """Anula una venta y restaura el stock (plan, reglas 9-13 y P14).

    Un movimiento compensatorio `entrada` por línea devuelve el inventario a
    `existencia`; el rastro de la venta se conserva por auditoría.
    """
    venta = await _obtener_venta(sesion, venta_id)
    if venta["estado"] == "anulada":
        raise VentaNoAnulableError("La venta ya fue anulada")

    autor = UUID(str(usuario_id))
    try:
        verificar_anulacion_venta(
            venta_usuario_id=str(venta["usuario_id"]),
            usuario_id=str(autor),
            rol=rol,
        )
    except PermissionError as error:
        raise AnulacionNoPermitidaError(str(error)) from error

    almacen_id = await obtener_almacen_por_defecto(sesion)

    async with sesion.begin_nested():
        await sesion.execute(
            text(
                """
                UPDATE venta
                SET estado = 'anulada', motivo_anulacion = :motivo
                WHERE id = :venta_id
                """
            ),
            {"motivo": datos.motivo_anulacion, "venta_id": venta_id},
        )

        lineas = (
            await sesion.execute(
                text(
                    """
                    SELECT producto_id, cantidad FROM detalle_venta
                    WHERE venta_id = :venta_id
                    """
                ),
                {"venta_id": venta_id},
            )
        ).mappings().all()

        for linea in lineas:
            await sesion.execute(
                text(
                    """
                    UPDATE existencia
                    SET cantidad = cantidad + :cantidad
                    WHERE producto_id = :producto_id AND almacen_id = :almacen_id
                    """
                ),
                {
                    "producto_id": linea["producto_id"],
                    "almacen_id": almacen_id,
                    "cantidad": linea["cantidad"],
                },
            )
            await sesion.execute(
                text(
                    """
                    INSERT INTO movimiento_inventario (
                        producto_id, almacen_id, tipo, referencia_tipo,
                        referencia_id, cantidad, usuario_id, nota
                    )
                    VALUES (
                        :producto_id, :almacen_id, 'entrada', 'venta',
                        :referencia_id, :cantidad, :usuario_id, :nota
                    )
                    """
                ),
                {
                    "producto_id": linea["producto_id"],
                    "almacen_id": almacen_id,
                    "referencia_id": venta_id,
                    "cantidad": linea["cantidad"],
                    "usuario_id": autor,
                    "nota": f"Anulación: {datos.motivo_anulacion}",
                },
            )

    return await _leer_venta(sesion, venta_id)


async def listar_ventas(
    sesion: AsyncSession, limite: int = 50, desplazamiento: int = 0
) -> list[VentaRead]:
    filas = (
        await sesion.execute(
            text(
                f"{SELECCION_VENTA} "
                "ORDER BY v.fecha DESC, v.id DESC "
                "LIMIT :limite OFFSET :desplazamiento"
            ),
            {"limite": limite, "desplazamiento": desplazamiento},
        )
    ).mappings().all()
    if not filas:
        return []

    ids = [fila["id"] for fila in filas]
    lineas = (
        await sesion.execute(
            text(
                """
                SELECT dv.venta_id, dv.producto_id, p.nombre AS producto_nombre,
                       dv.cantidad, dv.precio_unitario, dv.subtotal
                FROM detalle_venta dv
                JOIN producto p ON p.id = dv.producto_id
                WHERE dv.venta_id = ANY(:venta_ids)
                ORDER BY dv.venta_id, dv.id
                """
            ),
            {"venta_ids": ids},
        )
    ).mappings().all()

    por_venta: dict[UUID, list[VentaDetalleRead]] = {}
    for fila in lineas:
        por_venta.setdefault(fila["venta_id"], []).append(
            VentaDetalleRead(
                producto_id=fila["producto_id"],
                producto_nombre=fila["producto_nombre"],
                cantidad=fila["cantidad"],
                precio_unitario=fila["precio_unitario"],
                subtotal=fila["subtotal"],
            )
        )
    return [
        VentaRead(**dict(fila), lineas=por_venta.get(fila["id"], [])) for fila in filas
    ]


async def resumen_ventas(
    sesion: AsyncSession, fecha_inicio: date, fecha_fin: date
) -> ResumenVentas:
    """Ventas por día (hora de Guatemala) entre dos fechas, con días en 0.

    Solo cuenta ventas con `estado = 'activa'`. `generate_series` rellena los
    días sin ventas con 0 para que el gráfico del panel no tenga huecos.
    """
    filas = (
        await sesion.execute(
            text(
                """
                WITH dias AS (
                    SELECT generate_series(
                        CAST(:fecha_inicio AS date),
                        CAST(:fecha_fin AS date),
                        interval '1 day'
                    )::date AS dia
                ),
                agrupado AS (
                    SELECT (v.fecha AT TIME ZONE 'America/Guatemala')::date AS dia,
                           COUNT(*) AS num_ventas,
                           SUM(v.total) AS total_vendido
                    FROM venta v
                    WHERE v.estado = 'activa'
                      AND (v.fecha AT TIME ZONE 'America/Guatemala')::date
                          BETWEEN CAST(:fecha_inicio AS date) AND CAST(:fecha_fin AS date)
                    GROUP BY 1
                )
                SELECT d.dia AS fecha,
                       COALESCE(a.num_ventas, 0) AS num_ventas,
                       COALESCE(a.total_vendido, 0)::numeric(12,2) AS total_vendido
                FROM dias d
                LEFT JOIN agrupado a ON a.dia = d.dia
                ORDER BY d.dia
                """
            ),
            {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
        )
    ).mappings().all()

    por_dia = [ResumenVentaDia(**dict(fila)) for fila in filas]
    return ResumenVentas(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        num_ventas=sum(dia.num_ventas for dia in por_dia),
        total_vendido=a_cuantia(sum((dia.total_vendido for dia in por_dia), Decimal("0.00"))),
        por_dia=por_dia,
    )