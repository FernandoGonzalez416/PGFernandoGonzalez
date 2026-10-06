from datetime import date
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import config
from app.core.dinero import a_cuantia
from app.core.errores import (
    CategoriaNoEncontradaError,
    CodigoProductoDuplicadoError,
    ProductoConExistenciasError,
    ProductoNoEncontradoError,
    ProveedorNoEncontradoError,
    VencimientoInvalidoError,
    _menciona_restriccion,
)
from app.schemas.existencia import ExistenciaRead
from app.schemas.producto import ProductoCreate, ProductoRead, ProductoUpdate

RESTRICCION_CODIGO_UNICO = "uq_producto_codigo"

CAMPOS_PRODUCTO = """
    p.id, p.codigo, p.nombre, p.descripcion, p.categoria_id, p.proveedor_id,
    p.precio_venta, p.precio_costo, p.unidad_medida, p.umbral_minimo,
    p.dias_vencimiento_aviso, p.fecha_vencimiento, p.fecha_ingreso, p.activo,
    p.created_at, p.updated_at,
    COALESCE(e.cantidad, 0)::numeric(12, 2) AS existencia
"""

SELECCION_BASE = f"""
    FROM producto p
    LEFT JOIN existencia e ON e.producto_id = p.id AND e.almacen_id = :almacen_id
"""


def _a_producto(fila) -> ProductoRead:
    return ProductoRead(**{clave: valor for clave, valor in fila.items()})


def _es_violacion_de_codigo(error: IntegrityError) -> bool:
    return _menciona_restriccion(error, RESTRICCION_CODIGO_UNICO)


async def obtener_almacen_por_defecto(sesion: AsyncSession) -> UUID:
    """Resuelve el almacén por defecto (P19). El cliente nunca manda `almacen_id`."""
    almacen_id = (
        await sesion.execute(
            text("SELECT id FROM almacen WHERE nombre = :nombre"),
            {"nombre": config.ALMACEN_PREDETERMINADO},
        )
    ).scalar_one_or_none()

    if almacen_id is None:
        raise RuntimeError(
            f"No existe el almacén '{config.ALMACEN_PREDETERMINADO}'. "
            "Ejecuta `python scripts/semilla.py` para sembrarlo."
        )
    return almacen_id


def _validar_vencimiento(fecha_vencimiento: date | None) -> None:
    if fecha_vencimiento is not None and fecha_vencimiento < date.today():
        raise VencimientoInvalidoError(
            f"La fecha de vencimiento {fecha_vencimiento.isoformat()} ya pasó; "
            "no se puede registrar un producto que ya venció"
        )


async def _verificar_referencias(
    sesion: AsyncSession,
    categoria_id: UUID,
    proveedor_id: UUID | None,
) -> None:
    existe = await sesion.execute(
        text("SELECT 1 FROM categoria WHERE id = :categoria_id"), {"categoria_id": categoria_id}
    )
    if existe.scalar_one_or_none() is None:
        raise CategoriaNoEncontradaError(str(categoria_id))

    if proveedor_id is not None:
        existe = await sesion.execute(
            text("SELECT 1 FROM proveedor WHERE id = :proveedor_id"),
            {"proveedor_id": proveedor_id},
        )
        if existe.scalar_one_or_none() is None:
            raise ProveedorNoEncontradoError(str(proveedor_id))


async def _impedir_desactivar(sesion: AsyncSession, producto_id: UUID) -> None:
    estado = (
        await sesion.execute(
            text(
                """
                SELECT
                    EXISTS (
                        SELECT 1 FROM existencia
                        WHERE producto_id = :producto_id AND cantidad > 0
                    ) AS tiene_stock,
                    EXISTS (
                        SELECT 1 FROM venta
                        WHERE estado = 'activa'
                          AND EXISTS (
                              SELECT 1 FROM detalle_venta d
                              WHERE d.venta_id = venta.id AND d.producto_id = :producto_id
                          )
                    ) AS tiene_ventas
                """
            ),
            {"producto_id": producto_id},
        )
    ).mappings().one()

    if estado["tiene_stock"]:
        raise ProductoConExistenciasError(
            "No se puede desactivar: el producto tiene existencias con cantidad mayor a 0"
        )
    if estado["tiene_ventas"]:
        raise ProductoConExistenciasError(
            "No se puede desactivar: el producto tiene ventas asociadas"
        )


async def crear_producto(
    sesion: AsyncSession, datos: ProductoCreate, usuario_id: UUID | str
) -> ProductoRead:
    datos = datos.cuantizado()
    _validar_vencimiento(datos.fecha_vencimiento)
    # `UsuarioAutenticado.id` llega como texto; asyncpg exige `uuid.UUID` para
    # una columna uuid, así que se normaliza en el borde del servicio.
    autor = UUID(str(usuario_id))

    try:
        async with sesion.begin_nested():
            await _verificar_referencias(sesion, datos.categoria_id, datos.proveedor_id)
            almacen_id = await obtener_almacen_por_defecto(sesion)

            fila = (
                await sesion.execute(
                    text(
                        """
                        INSERT INTO producto (
                            codigo, nombre, descripcion, categoria_id, proveedor_id,
                            precio_venta, precio_costo, unidad_medida, umbral_minimo,
                            dias_vencimiento_aviso, fecha_vencimiento, fecha_ingreso
                        )
                        VALUES (
                            :codigo, :nombre, :descripcion, :categoria_id, :proveedor_id,
                            :precio_venta, :precio_costo, :unidad_medida, :umbral_minimo,
                            :dias_vencimiento_aviso, :fecha_vencimiento,
                            COALESCE(:fecha_ingreso, CURRENT_DATE)
                        )
                        RETURNING id
                        """
                    ),
                    {
                        "codigo": datos.codigo,
                        "nombre": datos.nombre,
                        "descripcion": datos.descripcion,
                        "categoria_id": datos.categoria_id,
                        "proveedor_id": datos.proveedor_id,
                        "precio_venta": datos.precio_venta,
                        "precio_costo": datos.precio_costo,
                        "unidad_medida": datos.unidad_medida,
                        "umbral_minimo": datos.umbral_minimo,
                        "dias_vencimiento_aviso": datos.dias_vencimiento_aviso,
                        "fecha_vencimiento": datos.fecha_vencimiento,
                        "fecha_ingreso": datos.fecha_ingreso,
                    },
                )
            ).scalar_one()

            producto_id = UUID(str(fila))

            await sesion.execute(
                text(
                    """
                    INSERT INTO existencia (producto_id, almacen_id, cantidad)
                    VALUES (:producto_id, :almacen_id, :cantidad)
                    ON CONFLICT (producto_id, almacen_id) DO UPDATE
                    SET cantidad = existencia.cantidad + EXCLUDED.cantidad
                    """
                ),
                {
                    "producto_id": producto_id,
                    "almacen_id": almacen_id,
                    "cantidad": datos.cantidad_inicial,
                },
            )

            if datos.cantidad_inicial > 0:
                await sesion.execute(
                    text(
                        """
                        INSERT INTO movimiento_inventario (
                            producto_id, almacen_id, tipo, referencia_tipo,
                            referencia_id, cantidad, usuario_id, nota
                        )
                        VALUES (
                            :producto_id, :almacen_id, 'entrada', 'inicial',
                            :producto_id, :cantidad, :usuario_id, 'Alta de producto'
                        )
                        """
                    ),
                    {
                        "producto_id": producto_id,
                        "almacen_id": almacen_id,
                        "cantidad": datos.cantidad_inicial,
                        "usuario_id": autor,
                    },
                )

            return await _leer_producto(sesion, producto_id, almacen_id)
    except IntegrityError as error:
        if _es_violacion_de_codigo(error):
            raise CodigoProductoDuplicadoError(datos.codigo) from error
        raise


async def _leer_producto(
    sesion: AsyncSession, producto_id: UUID, almacen_id: UUID
) -> ProductoRead:
    fila = (
        await sesion.execute(
            text(f"SELECT {CAMPOS_PRODUCTO} {SELECCION_BASE} WHERE p.id = :producto_id"),
            {"producto_id": producto_id, "almacen_id": almacen_id},
        )
    ).mappings().first()
    if fila is None:
        raise ProductoNoEncontradoError(str(producto_id))
    return _a_producto(fila)


async def obtener_producto(sesion: AsyncSession, producto_id: UUID) -> ProductoRead:
    almacen_id = await obtener_almacen_por_defecto(sesion)
    return await _leer_producto(sesion, producto_id, almacen_id)


async def listar_productos(
    sesion: AsyncSession,
    q: str | None = None,
    categoria_id: UUID | None = None,
    incluir_inactivos: bool = False,
    limite: int = 50,
    desplazamiento: int = 0,
) -> list[ProductoRead]:
    almacen_id = await obtener_almacen_por_defecto(sesion)

    condiciones = ["(:incluir_inactivos OR p.activo = true)"]
    if q is not None:
        condiciones.append("(lower(p.nombre) LIKE :patron OR p.codigo = :texto)")
    if categoria_id is not None:
        condiciones.append("p.categoria_id = :categoria_id")

    fila = (
        await sesion.execute(
            text(
                f"""
                SELECT {CAMPOS_PRODUCTO}
                {SELECCION_BASE}
                WHERE {" AND ".join(condiciones)}
                ORDER BY p.nombre, p.codigo
                LIMIT :limite OFFSET :desplazamiento
                """
            ),
            {
                "almacen_id": almacen_id,
                "incluir_inactivos": incluir_inactivos,
                "texto": q,
                "patron": f"%{q.lower()}%" if q else None,
                "categoria_id": categoria_id,
                "limite": limite,
                "desplazamiento": desplazamiento,
            },
        )
    ).mappings().all()
    return [_a_producto(item) for item in fila]


async def actualizar_producto(
    sesion: AsyncSession, producto_id: UUID, datos: ProductoUpdate
) -> ProductoRead:
    if datos.fecha_vencimiento is not None:
        _validar_vencimiento(datos.fecha_vencimiento)

    async with sesion.begin_nested():
        actual = await obtener_producto(sesion, producto_id)
        if datos.activo is False and actual.activo:
            await _impedir_desactivar(sesion, producto_id)

        if datos.categoria_id is not None and datos.categoria_id != actual.categoria_id:
            await _verificar_referencias(sesion, datos.categoria_id, datos.proveedor_id)
        elif datos.proveedor_id is not None and datos.proveedor_id != actual.proveedor_id:
            existe = await sesion.execute(
                text("SELECT 1 FROM proveedor WHERE id = :proveedor_id"),
                {"proveedor_id": datos.proveedor_id},
            )
            if existe.scalar_one_or_none() is None:
                raise ProveedorNoEncontradoError(str(datos.proveedor_id))

        campos = {
            clave: valor
            for clave, valor in datos.model_dump(exclude_unset=True).items()
            if valor is not None
        }
        for clave in ("precio_venta", "precio_costo", "umbral_minimo"):
            if clave in campos:
                campos[clave] = a_cuantia(campos[clave])

        if campos:
            asignaciones = ", ".join(f"{clave} = :{clave}" for clave in campos)
            await sesion.execute(
                text(f"UPDATE producto SET {asignaciones} WHERE id = :producto_id"),
                {**campos, "producto_id": producto_id},
            )

    almacen_id = await obtener_almacen_por_defecto(sesion)
    return await _leer_producto(sesion, producto_id, almacen_id)


async def listar_existencias(
    sesion: AsyncSession, producto_id: UUID
) -> list[ExistenciaRead]:
    await obtener_producto(sesion, producto_id)

    filas = (
        await sesion.execute(
            text(
                """
                SELECT e.producto_id, e.almacen_id, a.nombre AS almacen_nombre,
                       e.cantidad, e.updated_at
                FROM existencia e
                JOIN almacen a ON a.id = e.almacen_id
                WHERE e.producto_id = :producto_id
                ORDER BY a.nombre
                """
            ),
            {"producto_id": producto_id},
        )
    ).mappings().all()
    return [ExistenciaRead(**dict(item)) for item in filas]