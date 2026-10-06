"""Siembra el almacén por defecto y un catálogo mínimo ficticio.

Herramienta local: no es un endpoint y no se expone por HTTP. Es idempotente,
así que ejecutarla dos veces no duplica nada ni falla.

Usa SQL de texto con `sqlalchemy.text()`, el mismo acceso a datos que
`app/core/security.py`: el proyecto no tiene una capa ORM.
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

RAIZ_DEL_REPOSITORIO = Path(__file__).resolve().parents[1]
if str(RAIZ_DEL_REPOSITORIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_DEL_REPOSITORIO))

from app.core import config  # noqa: E402
from app.core.dinero import a_cuantia  # noqa: E402

CATEGORIAS = [
    ("Cabello", "SIMULACION: categoría ficticia de prueba."),
    ("Rostro", "SIMULACION: categoría ficticia de prueba."),
]

PROVEEDOR = (
    "SIMULACION Distribuidor Norte",
    "Proveedor ficticio de prueba",
    "SIMULACION: entrega en 3 días hábiles.",
    a_cuantia("18.00"),
)

# codigo, nombre, categoria, precio_venta, precio_costo, umbral_minimo, cantidad_inicial
PRODUCTOS = [
    (
        "SIM-P001",
        "SIMULACION Shampoo 400ml",
        "Cabello",
        a_cuantia("55.00"),
        a_cuantia("32.00"),
        a_cuantia("5.00"),
        a_cuantia("24.00"),
    ),
    (
        "SIM-P002",
        "SIMULACION Crema facial 50g",
        "Rostro",
        a_cuantia("120.00"),
        a_cuantia("70.00"),
        a_cuantia("3.00"),
        a_cuantia("10.00"),
    ),
]

INSERTAR_ALMACEN = text(
    """
    INSERT INTO almacen (nombre, ubicacion)
    VALUES (:nombre, 'Almacén principal')
    ON CONFLICT (nombre) DO NOTHING
    RETURNING id
    """
)

INSERTAR_CATEGORIA = text(
    """
    INSERT INTO categoria (nombre, descripcion)
    VALUES (:nombre, :descripcion)
    ON CONFLICT (lower(nombre)) DO NOTHING
    RETURNING id
    """
)

INSERTAR_PROVEEDOR = text(
    """
    INSERT INTO proveedor (nombre, contacto, condiciones_entrega, precio_habitual)
    SELECT :nombre, :contacto, :condiciones_entrega, :precio_habitual
    WHERE NOT EXISTS (SELECT 1 FROM proveedor WHERE nombre = :nombre)
    RETURNING id
    """
)

INSERTAR_PRODUCTO = text(
    """
    INSERT INTO producto (
        codigo, nombre, descripcion, categoria_id, proveedor_id,
        precio_venta, precio_costo, umbral_minimo, fecha_ingreso
    )
    VALUES (
        :codigo, :nombre, 'SIMULACION: producto ficticio de prueba.', :categoria_id,
        :proveedor_id, :precio_venta, :precio_costo, :umbral_minimo, CURRENT_DATE
    )
    ON CONFLICT (codigo) DO NOTHING
    RETURNING id
    """
)

INSERTAR_EXISTENCIA = text(
    """
    INSERT INTO existencia (producto_id, almacen_id, cantidad)
    VALUES (:producto_id, :almacen_id, :cantidad)
    ON CONFLICT (producto_id, almacen_id) DO NOTHING
    RETURNING id
    """
)

INSERTAR_MOVIMIENTO = text(
    """
    INSERT INTO movimiento_inventario (
        producto_id, almacen_id, tipo, referencia_tipo, cantidad, nota
    )
    VALUES (:producto_id, :almacen_id, 'entrada', 'inicial', :cantidad, 'Carga inicial (SIMULACION)')
    """
)


async def sembrar() -> dict[str, int]:
    motor = create_async_engine(config.DATABASE_URL, pool_pre_ping=True)
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    creados = {"almacen": 0, "categorias": 0, "proveedores": 0, "productos": 0,
               "existencias": 0, "movimientos": 0}

    async with fabrica() as sesion:
        async with sesion.begin():
            resultado = await sesion.execute(INSERTAR_ALMACEN, {"nombre": config.ALMACEN_PREDETERMINADO})
            almacen_id = resultado.scalar_one_or_none()
            if almacen_id is None:
                almacen_id = (
                    await sesion.execute(
                        text("SELECT id FROM almacen WHERE nombre = :nombre"),
                        {"nombre": config.ALMACEN_PREDETERMINADO},
                    )
                ).scalar_one()
            else:
                creados["almacen"] = 1

            categoria_ids: dict[str, object] = {}
            for nombre, descripcion in CATEGORIAS:
                resultado = await sesion.execute(
                    INSERTAR_CATEGORIA, {"nombre": nombre, "descripcion": descripcion}
                )
                categoria_id = resultado.scalar_one_or_none()
                if categoria_id is None:
                    categoria_id = (
                        await sesion.execute(
                            text("SELECT id FROM categoria WHERE lower(nombre) = lower(:nombre)"),
                            {"nombre": nombre},
                        )
                    ).scalar_one()
                else:
                    creados["categorias"] += 1
                categoria_ids[nombre] = categoria_id

            nombre_proveedor, contacto, condiciones, precio = PROVEEDOR
            resultado = await sesion.execute(
                INSERTAR_PROVEEDOR,
                {
                    "nombre": nombre_proveedor,
                    "contacto": contacto,
                    "condiciones_entrega": condiciones,
                    "precio_habitual": precio,
                },
            )
            proveedor_id = resultado.scalar_one_or_none()
            if proveedor_id is None:
                proveedor_id = (
                    await sesion.execute(
                        text("SELECT id FROM proveedor WHERE nombre = :nombre"),
                        {"nombre": nombre_proveedor},
                    )
                ).scalar_one()
            else:
                creados["proveedores"] = 1

            for codigo, nombre, categoria, precio_venta, precio_costo, umbral, cantidad in PRODUCTOS:
                resultado = await sesion.execute(
                    INSERTAR_PRODUCTO,
                    {
                        "codigo": codigo,
                        "nombre": nombre,
                        "categoria_id": categoria_ids[categoria],
                        "proveedor_id": proveedor_id,
                        "precio_venta": precio_venta,
                        "precio_costo": precio_costo,
                        "umbral_minimo": umbral,
                    },
                )
                producto_id = resultado.scalar_one_or_none()
                if producto_id is None:
                    producto_id = (
                        await sesion.execute(
                            text("SELECT id FROM producto WHERE codigo = :codigo"),
                            {"codigo": codigo},
                        )
                    ).scalar_one()
                    continue

                creados["productos"] += 1
                existencia = await sesion.execute(
                    INSERTAR_EXISTENCIA,
                    {"producto_id": producto_id, "almacen_id": almacen_id, "cantidad": cantidad},
                )
                if existencia.scalar_one_or_none() is not None:
                    creados["existencias"] += 1
                    await sesion.execute(
                        INSERTAR_MOVIMIENTO,
                        {
                            "producto_id": producto_id,
                            "almacen_id": almacen_id,
                            "cantidad": cantidad,
                        },
                    )
                    creados["movimientos"] += 1

    await motor.dispose()
    return creados


def main() -> None:
    resultado = asyncio.run(sembrar())
    total = sum(resultado.values())
    print("SIMULACION: datos ficticios de prueba, no son datos reales del negocio.")
    print(f"almacen '{config.ALMACEN_PREDETERMINADO}': {resultado['almacen']} creados")
    for clave in ("categorias", "proveedores", "productos", "existencias", "movimientos"):
        print(f"{clave}: {resultado[clave]} creados")
    print(f"total creados: {total}")


if __name__ == "__main__":
    main()