"""Siembra datos de DEMOSTRACIÓN (SIMULACION) para el piloto de la F2.

Herramienta local: no es un endpoint y no se expone por HTTP. Es un archivo
**independiente** de `semilla.py`: no lo modifica ni lo sustituye.

Qué siembra:

- 5 categorías, 3 proveedores y 20 productos ficticios (códigos `SIM-`).
- 30 días de ventas (3 a 8 por día, 1 a 3 líneas), con métodos de pago
  variados, algunos descuentos y repartidas entre los 3 usuarios del sistema.
- 3 ventas anuladas con motivo.
- Estado final buscado: 4 productos con existencia <= umbral (uno en 0), 2 con
  vencimiento a menos de 10 días y 1 ya vencido.

Todos los datos están marcados con `SIMULACION` y **no son datos reales del
negocio** (P4). La semántica de negocio se ejerce con los servicios del backend
(`crear_producto`, `registrar_venta`, `anular_venta`, `ajustar_existencia`); el
único acceso directo por SQL es el retraso de fechas al día que corresponde y el
vencimiento ya pasado (que el alta rechazaría por diseño).

Idempotente: si ya existen productos `SIM-`, no siembra nada más.

Requiere en `backend/.env`: `DATABASE_URL` (base de **desarrollo**). Nunca se
ejecuta contra el esquema de pruebas.
"""

import asyncio
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

RAIZ_DEL_REPOSITORIO = Path(__file__).resolve().parents[1]
if str(RAIZ_DEL_REPOSITORIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_DEL_REPOSITORIO))

from app.core import config  # noqa: E402
from app.core.dinero import a_cuantia  # noqa: E402
from app.schemas.existencia import ExistenciaAjuste  # noqa: E402
from app.schemas.producto import ProductoCreate  # noqa: E402
from app.schemas.venta import AnulacionCreate, VentaCreate, VentaDetalleCreate  # noqa: E402
from app.services.existencia import ajustar_existencia  # noqa: E402
from app.services.productos import crear_producto  # noqa: E402
from app.services.ventas import anular_venta, registrar_venta  # noqa: E402

SEMILLA_ALEATORIA = 20261009
DIAS_DE_VENTAS = 30
VENTAS_ANULADAS = 3

CATEGORIAS = [
    ("Cabello", "SIMULACION: categoría ficticia de prueba."),
    ("Rostro", "SIMULACION: categoría ficticia de prueba."),
    ("Maquillaje", "SIMULACION: categoría ficticia de prueba."),
    ("Uñas", "SIMULACION: categoría ficticia de prueba."),
    ("Cuidado personal", "SIMULACION: categoría ficticia de prueba."),
]

# nombre, contacto, condiciones_entrega, precio_habitual
PROVEEDORES = [
    (
        "SIMULACION Distribuidor Norte",
        "Ventas Zona 3",
        "SIMULACION: entrega en 3 días hábiles.",
        a_cuantia("18.00"),
    ),
    (
        "SIMULACION Belleza Total",
        "Compras Mayoreo",
        "SIMULACION: entrega en 5 días hábiles.",
        a_cuantia("22.00"),
    ),
    (
        "SIMULACION Importadora Centroamericana",
        "Atención a distribuidores",
        "SIMULACION: pedido mínimo de Q500.",
        a_cuantia("25.00"),
    ),
]

# codigo, nombre, categoria, proveedor, precio_venta, precio_costo, umbral, stock_inicial
PRODUCTOS = [
    ("SIM-001", "SIMULACION Shampoo anticaída 400 ml", "Cabello", 0, "65.00", "38.00", "6.00", "140.00"),
    ("SIM-002", "SIMULACION Acondicionador hidratante 400 ml", "Cabello", 0, "68.00", "40.00", "6.00", "130.00"),
    ("SIM-003", "SIMULACION Mascarilla capilar keratina 250 g", "Cabello", 1, "95.00", "55.00", "4.00", "80.00"),
    ("SIM-004", "SIMULACION Sérum anticaída 30 ml", "Cabello", 0, "120.00", "70.00", "4.00", "70.00"),
    ("SIM-005", "SIMULACION Crema facial hidratante 50 g", "Rostro", 1, "110.00", "62.00", "5.00", "110.00"),
    ("SIM-006", "SIMULACION Protector solar SPF50 50 ml", "Rostro", 1, "145.00", "85.00", "5.00", "100.00"),
    ("SIM-007", "SIMULACION Limpiador facial espuma 150 ml", "Rostro", 2, "88.00", "48.00", "6.00", "120.00"),
    ("SIM-008", "SIMULACION Agua micelar 400 ml", "Rostro", 2, "75.00", "42.00", "6.00", "130.00"),
    ("SIM-009", "SIMULACION Contorno de ojos 15 ml", "Rostro", 1, "130.00", "78.00", "3.00", "60.00"),
    ("SIM-010", "SIMULACION Base líquida 30 ml", "Maquillaje", 2, "135.00", "80.00", "4.00", "80.00"),
    ("SIM-011", "SIMULACION Labial mate larga duración", "Maquillaje", 2, "55.00", "28.00", "8.00", "180.00"),
    ("SIM-012", "SIMULACION Máscara de pestañas volumen", "Maquillaje", 1, "85.00", "45.00", "5.00", "100.00"),
    ("SIM-013", "SIMULACION Rubor en polvo", "Maquillaje", 2, "78.00", "42.00", "5.00", "95.00"),
    ("SIM-014", "SIMULACION Paleta de sombras 12 tonos", "Maquillaje", 2, "165.00", "98.00", "3.00", "55.00"),
    ("SIM-015", "SIMULACION Esmalte de uñas gel", "Uñas", 1, "45.00", "22.00", "10.00", "220.00"),
    ("SIM-016", "SIMULACION Quitaesmalte sin acetona 100 ml", "Uñas", 1, "35.00", "18.00", "10.00", "200.00"),
    ("SIM-017", "SIMULACION Crema para manos 75 ml", "Cuidado personal", 0, "42.00", "21.00", "8.00", "160.00"),
    ("SIM-018", "SIMULACION Gel antibacterial 250 ml", "Cuidado personal", 0, "30.00", "15.00", "12.00", "240.00"),
    ("SIM-019", "SIMULACION Desodorante roll-on 50 ml", "Cuidado personal", 0, "38.00", "20.00", "10.00", "170.00"),
    ("SIM-020", "SIMULACION Crema corporal reparadora 400 ml", "Cuidado personal", 1, "98.00", "55.00", "5.00", "110.00"),
]

# product_id -> existencia final buscada (uno queda en 0)
STOCK_FINAL_BAJO = {
    "SIM-004": Decimal("0.00"),
    "SIM-009": Decimal("2.00"),
    "SIM-013": Decimal("4.00"),
    "SIM-020": Decimal("3.00"),
}

# product_id -> días de vencimiento respecto de hoy (negativo = ya vencido)
VENCIMIENTOS = {
    "SIM-006": 7,
    "SIM-010": 9,
    "SIM-005": -4,
}

METODOS_DE_PAGO = ["efectivo", "tarjeta", "transferencia", "otro"]

USUARIOS_REQUERIDOS = [
    ("fer@gmail.com", "administrador"),
    ("propietario@prueba.com", "propietario"),
    ("padre@prueba.com", "padre"),
]

# Códigos propios de esta siembra. `semilla.py` usa `SIM-P...`; la demostración
# usa `SIM-0...`, así que ambos scripts pueden convivir sin chocar.
CODIGOS_DEMO = [fila[0] for fila in PRODUCTOS]


async def _esquema_actual(sesion) -> str:
    return (await sesion.execute(text("SELECT current_schema()"))).scalar_one()


async def _almacen_principal(sesion) -> UUID:
    almacen_id = (
        await sesion.execute(
            text("SELECT id FROM almacen WHERE nombre = :nombre"),
            {"nombre": config.ALMACEN_PREDETERMINADO},
        )
    ).scalar_one_or_none()
    if almacen_id is None:
        raise SystemExit(
            f"No existe el almacén '{config.ALMACEN_PREDETERMINADO}'. "
            "Ejecuta primero `python scripts/semilla.py`."
        )
    return UUID(str(almacen_id))


async def _usuarios(sesion) -> dict[str, dict[str, str]]:
    usuarios: dict[str, dict[str, str]] = {}
    for email, rol_esperado in USUARIOS_REQUERIDOS:
        fila = (
            await sesion.execute(
                text("SELECT id, rol FROM usuario WHERE email = :email AND activo = true"),
                {"email": email},
            )
        ).mappings().one_or_none()
        if fila is None:
            raise SystemExit(
                f"Falta el usuario '{email}' (rol {rol_esperado}). "
                "Ejecuta primero `python scripts/crear_usuarios_prueba.py`."
            )
        usuarios[email] = {"id": str(fila["id"]), "rol": fila["rol"]}
    return usuarios


async def _obtener_o_crear_categoria(sesion, nombre: str, descripcion: str) -> tuple[UUID, bool]:
    existente = (
        await sesion.execute(
            text("SELECT id FROM categoria WHERE lower(nombre) = lower(:nombre)"),
            {"nombre": nombre},
        )
    ).scalar_one_or_none()
    if existente is not None:
        return UUID(str(existente)), False
    nueva = (
        await sesion.execute(
            text(
                """
                INSERT INTO categoria (nombre, descripcion)
                VALUES (:nombre, :descripcion)
                RETURNING id
                """
            ),
            {"nombre": nombre, "descripcion": descripcion},
        )
    ).scalar_one()
    return UUID(str(nueva)), True


async def _obtener_o_crear_proveedor(
    sesion, nombre: str, contacto: str, condiciones: str, precio: Decimal
) -> tuple[UUID, bool]:
    existente = (
        await sesion.execute(
            text("SELECT id FROM proveedor WHERE nombre = :nombre"),
            {"nombre": nombre},
        )
    ).scalar_one_or_none()
    if existente is not None:
        return UUID(str(existente)), False
    nuevo = (
        await sesion.execute(
            text(
                """
                INSERT INTO proveedor (nombre, contacto, condiciones_entrega, precio_habitual)
                VALUES (:nombre, :contacto, :condiciones, :precio)
                RETURNING id
                """
            ),
            {
                "nombre": nombre,
                "contacto": contacto,
                "condiciones": condiciones,
                "precio": precio,
            },
        )
    ).scalar_one()
    return UUID(str(nuevo)), True


async def _hay_productos_demo(sesion) -> bool:
    return (
        await sesion.execute(
            text("SELECT EXISTS (SELECT 1 FROM producto WHERE codigo = ANY(:codigos))"),
            {"codigos": CODIGOS_DEMO},
        )
    ).scalar_one()


async def _contar_por_tabla(sesion) -> dict[str, int]:
    fila = (
        await sesion.execute(
            text(
                """
                SELECT
                    (SELECT count(*) FROM categoria) AS categorias,
                    (SELECT count(*) FROM proveedor) AS proveedores,
                    (SELECT count(*) FROM producto) AS productos,
                    (SELECT count(*) FROM producto WHERE codigo = ANY(:codigos)) AS productos_demo,
                    (SELECT count(*) FROM existencia) AS existencias,
                    (SELECT count(*) FROM venta) AS ventas,
                    (SELECT count(*) FROM venta WHERE estado = 'anulada') AS ventas_anuladas,
                    (SELECT count(*) FROM detalle_venta) AS detalles_venta,
                    (SELECT count(*) FROM movimiento_inventario) AS movimientos
                """
            ),
            {"codigos": CODIGOS_DEMO},
        )
    ).mappings().one()
    return {clave: int(valor) for clave, valor in fila.items()}


def _quantizado(valor: str) -> Decimal:
    return a_cuantia(valor)


async def _sembrar(sesion) -> dict[str, int]:
    random.seed(SEMILLA_ALEATORIA)

    await _almacen_principal(sesion)  # falla temprano si no hay almacén
    usuarios = await _usuarios(sesion)
    usuario_ids = [datos["id"] for datos in usuarios.values()]
    roles_por_usuario = {datos["id"]: datos["rol"] for datos in usuarios.values()}
    autor_admin = usuario_ids[0]

    resumen = {
        "categorias_creadas": 0,
        "proveedores_creados": 0,
        "productos_creados": 0,
        "ventas_creadas": 0,
        "ventas_anuladas": 0,
        "ajustes_aplicados": 0,
    }

    categoria_ids: dict[str, UUID] = {}
    for nombre, descripcion in CATEGORIAS:
        categoria_id, creada = await _obtener_o_crear_categoria(sesion, nombre, descripcion)
        categoria_ids[nombre] = categoria_id
        resumen["categorias_creadas"] += int(creada)

    proveedor_ids: list[UUID] = []
    for nombre, contacto, condiciones, precio in PROVEEDORES:
        proveedor_id, creado = await _obtener_o_crear_proveedor(
            sesion, nombre, contacto, condiciones, precio
        )
        proveedor_ids.append(proveedor_id)
        resumen["proveedores_creados"] += int(creado)

    producto_ids: dict[str, UUID] = {}
    precios: dict[str, Decimal] = {}
    for codigo, nombre, categoria, proveedor, precio, costo, umbral, stock in PRODUCTOS:
        producto = await crear_producto(
            sesion,
            ProductoCreate(
                codigo=codigo,
                nombre=nombre,
                descripcion="SIMULACION: producto ficticio de prueba.",
                categoria_id=categoria_ids[categoria],
                proveedor_id=proveedor_ids[proveedor],
                precio_venta=_quantizado(precio),
                precio_costo=_quantizado(costo),
                umbral_minimo=_quantizado(umbral),
                dias_vencimiento_aviso=10,
                cantidad_inicial=_quantizado(stock),
            ),
            autor_admin,
        )
        producto_ids[codigo] = producto.id
        precios[codigo] = a_cuantia(producto.precio_venta)
        resumen["productos_creados"] += 1

    codigos = list(producto_ids.keys())
    restante = {fila[0]: a_cuantia(fila[7]) for fila in PRODUCTOS}
    hoy = date.today()
    ventas: list[dict[str, object]] = []

    for indice_dia in range(DIAS_DE_VENTAS):
        dia = hoy - timedelta(days=DIAS_DE_VENTAS - 1 - indice_dia)
        for _ in range(random.randint(3, 8)):
            disponibles = [codigo for codigo in codigos if restante[codigo] >= 1]
            if not disponibles:
                break
            elegidos = random.sample(disponibles, min(random.randint(1, 3), len(disponibles)))
            lineas: list[VentaDetalleCreate] = []
            subtotal = Decimal("0.00")
            for codigo in elegidos:
                cantidad = random.randint(1, 2)
                if restante[codigo] < cantidad:
                    cantidad = int(restante[codigo])
                if cantidad < 1:
                    continue
                restante[codigo] -= cantidad
                lineas.append(
                    VentaDetalleCreate(producto_id=producto_ids[codigo], cantidad=cantidad)
                )
                # El descuento se decide sobre un subtotal calculado aquí; el
                # backend es la autoridad del total y lo recalcula.
                subtotal += precios[codigo] * cantidad
            if not lineas:
                continue
            subtotal = a_cuantia(subtotal)
            descuento = (
                a_cuantia("5.00")
                if random.random() < 0.3 and subtotal >= a_cuantia("5.00")
                else Decimal("0.00")
            )
            autor = random.choice(usuario_ids)
            venta = await registrar_venta(
                sesion,
                VentaCreate(
                    lineas=lineas,
                    descuento=descuento,
                    metodo_pago=random.choice(METODOS_DE_PAGO),
                    cliente_id=None,
                ),
                UUID(autor),
            )
            ventas.append(
                {
                    "id": venta.id,
                    "dia": dia,
                    "usuario_id": autor,
                    "rol": roles_por_usuario[autor],
                }
            )
            resumen["ventas_creadas"] += 1
        print(
            f"  día {indice_dia + 1}/{DIAS_DE_VENTAS}: ventas acumuladas={len(ventas)}",
            flush=True,
        )

    for indice in random.sample(range(len(ventas)), VENTAS_ANULADAS):
        objetivo = ventas[indice]
        await anular_venta(
            sesion,
            UUID(str(objetivo["id"])),
            UUID(str(objetivo["usuario_id"])),
            str(objetivo["rol"]),
            AnulacionCreate(motivo_anulacion="SIMULACION: anulación de demostración"),
        )
        resumen["ventas_anuladas"] += 1

    for venta in ventas:
        momento = datetime(venta["dia"].year, venta["dia"].month, venta["dia"].day, 12, 0, 0)
        await sesion.execute(
            text("UPDATE venta SET fecha = :fecha WHERE id = :venta_id"),
            {"fecha": momento, "venta_id": venta["id"]},
        )
        await sesion.execute(
            text(
                """
                UPDATE movimiento_inventario
                SET fecha = :fecha
                WHERE referencia_id = :venta_id AND referencia_tipo = 'venta'
                """
            ),
            {"fecha": momento, "venta_id": venta["id"]},
        )

    for codigo, dias in VENCIMIENTOS.items():
        await sesion.execute(
            text("UPDATE producto SET fecha_vencimiento = :fecha WHERE id = :producto_id"),
            {"fecha": hoy + timedelta(days=dias), "producto_id": producto_ids[codigo]},
        )

    for codigo, objetivo in STOCK_FINAL_BAJO.items():
        producto_id = producto_ids[codigo]
        actual = (
            await sesion.execute(
                text("SELECT cantidad FROM existencia WHERE producto_id = :producto_id"),
                {"producto_id": producto_id},
            )
        ).scalar_one()
        delta = a_cuantia(objetivo - a_cuantia(actual))
        if delta == 0:
            continue
        await ajustar_existencia(
            sesion,
            ExistenciaAjuste(
                producto_id=producto_id,
                cantidad=delta,
                nota="SIMULACION: ajuste de demostración para dejar stock bajo",
            ),
            UUID(autor_admin),
        )
        resumen["ajustes_aplicados"] += 1

    return resumen


async def sembrar() -> dict[str, int]:
    motor = create_async_engine(config.DATABASE_URL, pool_pre_ping=True)
    fabrica = async_sessionmaker(motor, expire_on_commit=False)

    async with fabrica() as sesion:
        async with sesion.begin():
            if await _esquema_actual(sesion) == "test":
                raise SystemExit(
                    "DATABASE_URL apunta al esquema 'test'. La demostración solo "
                    "se siembra en la base de desarrollo."
                )
            if await _hay_productos_demo(sesion):
                print("Ya existen productos de la demostración: no se siembra de nuevo (idempotente).")
            else:
                resumen = await _sembrar(sesion)
                print("Creación durante la siembra:")
                for clave, valor in resumen.items():
                    print(f"  {clave}: {valor}")

        conteos = await _contar_por_tabla(sesion)

    await motor.dispose()
    return conteos


def main() -> None:
    conteos = asyncio.run(sembrar())
    print("")
    print("SIMULACION: datos ficticios de prueba, no son datos reales del negocio.")
    print("Conteos por tabla:")
    for clave, valor in conteos.items():
        print(f"  {clave}: {valor}")


if __name__ == "__main__":
    main()
