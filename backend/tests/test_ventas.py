import re
from decimal import Decimal
from uuid import UUID, uuid4

import httpx2
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import simular_rol

from app.main import app
from app.schemas.producto import ProductoCreate
from app.services import productos as servicio_productos

pytestmark = pytest.mark.integracion


async def _crear_categoria(sesion: AsyncSession) -> UUID:
    return (
        await sesion.execute(
            text("INSERT INTO categoria (nombre) VALUES (:nombre) RETURNING id"),
            {"nombre": f"Cat-{uuid4().hex[:8]}"},
        )
    ).scalar_one()


async def _crear_producto(
    sesion: AsyncSession,
    usuario_id: UUID,
    precio_venta=Decimal("55.00"),
    cantidad_inicial=Decimal("10.00"),
) -> UUID:
    producto = await servicio_productos.crear_producto(
        sesion,
        ProductoCreate(
            codigo=f"P-{uuid4().hex[:8]}",
            nombre="Shampoo 400ml",
            categoria_id=await _crear_categoria(sesion),
            precio_venta=precio_venta,
            precio_costo=Decimal("32.00"),
            umbral_minimo=Decimal("5.00"),
            cantidad_inicial=cantidad_inicial,
        ),
        usuario_id,
    )
    return producto.id


async def _cantidad(sesion: AsyncSession, producto_id: UUID) -> Decimal:
    return (
        await sesion.execute(
            text(
                "SELECT cantidad FROM existencia WHERE producto_id = :producto_id"
            ),
            {"producto_id": producto_id},
        )
    ).scalar_one()


async def _movimientos(sesion: AsyncSession, producto_id: UUID) -> list[dict]:
    filas = (
        await sesion.execute(
            text(
                """
                SELECT tipo, referencia_tipo, cantidad, nota
                FROM movimiento_inventario
                WHERE producto_id = :producto_id
                ORDER BY fecha, id
                """
            ),
            {"producto_id": producto_id},
        )
    ).mappings().all()
    return [dict(fila) for fila in filas]


async def _post_venta(
    sesion: AsyncSession, rol: str, usuario_id: UUID, cuerpo: dict
) -> httpx2.Response:
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app),
            base_url="http://pruebas",
        ) as cliente:
            return await cliente.post("/api/ventas", json=cuerpo)
    finally:
        app.dependency_overrides.clear()


def _linea(producto_id: UUID, cantidad: int) -> dict:
    return {"producto_id": str(producto_id), "cantidad": cantidad}


class TestRegistroDeVenta:
    async def test_venta_simple_resta_stock_y_deja_movimiento_salida(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)

        respuesta = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 3)]},
        )

        assert respuesta.status_code == 201
        cuerpo = respuesta.json()
        assert re.fullmatch(r"^F-\d{4}-\d{4,}$", cuerpo["folio"])
        assert cuerpo["subtotal"] == "165.00"
        assert cuerpo["descuento"] == "0.00"
        assert cuerpo["total"] == "165.00"
        assert cuerpo["estado"] == "activa"
        assert cuerpo["metodo_pago"] == "efectivo"
        assert len(cuerpo["lineas"]) == 1
        assert cuerpo["lineas"][0]["producto_nombre"] == "Shampoo 400ml"
        assert cuerpo["lineas"][0]["precio_unitario"] == "55.00"
        assert cuerpo["lineas"][0]["cantidad"] == 3

        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("7.00")
        movimientos = await _movimientos(sesion_de_pruebas, producto_id)
        assert len(movimientos) == 2
        salida = next(m for m in movimientos if m["tipo"] == "salida")
        assert salida["referencia_tipo"] == "venta"
        assert salida["cantidad"] == 3

    async def test_venta_con_dos_lineas_y_descuento_calcula_totales(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        barato = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, precio_venta=Decimal("55.00")
        )
        caro = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, precio_venta=Decimal("100.00")
        )

        respuesta = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {
                "lineas": [_linea(barato, 2), _linea(caro, 1)],
                "descuento": "10.00",
            },
        )

        assert respuesta.status_code == 201
        cuerpo = respuesta.json()
        assert cuerpo["subtotal"] == "210.00"
        assert cuerpo["descuento"] == "10.00"
        assert cuerpo["total"] == "200.00"
        assert await _cantidad(sesion_de_pruebas, barato) == Decimal("8.00")
        assert await _cantidad(sesion_de_pruebas, caro) == Decimal("9.00")

    async def test_stock_insuficiente_no_deja_rastro(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
        conteos = [
            (await sesion_de_pruebas.execute(text("SELECT count(*) FROM venta"))).scalar_one(),
            (
                await sesion_de_pruebas.execute(
                    text("SELECT count(*) FROM detalle_venta")
                )
            ).scalar_one(),
            (
                await sesion_de_pruebas.execute(
                    text("SELECT count(*) FROM movimiento_inventario")
                )
            ).scalar_one(),
        ]

        respuesta = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 11)]},
        )

        assert respuesta.status_code == 409
        assert "Shampoo 400ml" in respuesta.json()["detail"]
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("10.00")
        assert (
            (await sesion_de_pruebas.execute(text("SELECT count(*) FROM venta"))).scalar_one()
            == conteos[0]
        )
        assert (
            (
                await sesion_de_pruebas.execute(
                    text("SELECT count(*) FROM detalle_venta")
                )
            ).scalar_one()
            == conteos[1]
        )
        assert (
            (
                await sesion_de_pruebas.execute(
                    text("SELECT count(*) FROM movimiento_inventario")
                )
            ).scalar_one()
            == conteos[2]
        )

    async def test_lineas_duplicadas_se_fusionan_en_una_sola(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)

        respuesta = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 2), _linea(producto_id, 3)]},
        )

        assert respuesta.status_code == 201
        cuerpo = respuesta.json()
        assert len(cuerpo["lineas"]) == 1
        assert cuerpo["lineas"][0]["cantidad"] == 5
        assert cuerpo["subtotal"] == "275.00"
        assert (
            (await sesion_de_pruebas.execute(
                        text(
                            "SELECT count(*) FROM detalle_venta "
                            f"WHERE venta_id = '{cuerpo['id']}'"
                        )
                    )
            ).scalar_one()
            == 1
        )
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("5.00")

    async def test_precio_no_viaja_en_el_request(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)

        respuesta = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {
                "lineas": [_linea(producto_id, 1)],
                "precio_unitario": "1.00",
            },
        )

        assert respuesta.status_code == 422

    async def test_producto_inexistente_devuelve_404(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        respuesta = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(uuid4(), 1)]},
        )

        assert respuesta.status_code == 404

    async def test_venta_sin_lineas_devuelve_422(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        respuesta = await _post_venta(
            sesion_de_pruebas, "propietario", usuario_de_pruebas, {"lineas": []}
        )

        assert respuesta.status_code == 422

    async def test_cantidad_cero_o_metodo_de_pago_invalido_devuelven_422(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)

        sin_cantidad = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 0)]},
        )
        metodo_invalido = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 1)], "metodo_pago": "bitcoin"},
        )
        descuento_negativo = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 1)], "descuento": "-1.00"},
        )

        assert sin_cantidad.status_code == 422
        assert metodo_invalido.status_code == 422
        assert descuento_negativo.status_code == 422

    async def test_folio_incremental_en_el_anio(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
        primer_cuerpo = {
            "lineas": [_linea(producto_id, 1)]
        }

        primera = await _post_venta(
            sesion_de_pruebas, "propietario", usuario_de_pruebas, primer_cuerpo
        )
        segunda = await _post_venta(
            sesion_de_pruebas, "propietario", usuario_de_pruebas, primer_cuerpo
        )

        assert primera.status_code == 201
        assert segunda.status_code == 201
        anio = re.search(r"^F-(\d{4})-", primera.json()["folio"]).group(1)
        assert primera.json()["folio"] == f"F-{anio}-0001"
        assert segunda.json()["folio"] == f"F-{anio}-0002"


class TestClienteEnLaVenta:
    async def test_venta_guarda_el_cliente_id(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        cliente_id = (
            await sesion_de_pruebas.execute(
                text("INSERT INTO cliente (nombre) VALUES ('María') RETURNING id")
            )
        ).scalar_one()
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)

        respuesta = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 1)], "cliente_id": str(cliente_id)},
        )

        assert respuesta.status_code == 201
        assert respuesta.json()["cliente_id"] == str(cliente_id)

    async def test_cliente_inactivo_o_inexistente_devuelve_422(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        inactivo = (
            await sesion_de_pruebas.execute(
                text(
                    "INSERT INTO cliente (nombre, activo) "
                    "VALUES ('Inactiva', FALSE) RETURNING id"
                )
            )
        ).scalar_one()
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)

        inexistente = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 1)], "cliente_id": str(uuid4())},
        )
        desactivado = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 1)], "cliente_id": str(inactivo)},
        )

        assert inexistente.status_code == 422
        assert desactivado.status_code == 422


class TestConsultaDeVentas:
    async def test_obtener_venta_por_id(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
        creada = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 2)]},
        )
        venta_id = creada.json()["id"]

        simular_rol(sesion_de_pruebas, "propietario", usuario_de_pruebas)
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.get(f"/api/ventas/{venta_id}")
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 200
        assert respuesta.json()["id"] == venta_id
        assert respuesta.json()["lineas"][0]["producto_nombre"] == "Shampoo 400ml"

    async def test_obtener_venta_inexistente_devuelve_404(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        simular_rol(sesion_de_pruebas, "propietario", usuario_de_pruebas)
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.get(f"/api/ventas/{uuid4()}")
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 404

    async def test_listado_paginado_ordenado_por_fecha_desc(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
        folios = [
            (
                await _post_venta(
                    sesion_de_pruebas,
                    "propietario",
                    usuario_de_pruebas,
                    {"lineas": [_linea(producto_id, 1)]},
                )
            ).json()["folio"]
            for _ in range(3)
        ]

        await sesion_de_pruebas.execute(
            text(
                "UPDATE venta SET fecha = fecha - interval '2 days' "
                "WHERE folio = :folio"
            ),
            {"folio": folios[0]},
        )

        simular_rol(sesion_de_pruebas, "propietario", usuario_de_pruebas)
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                primera = await cliente.get("/api/ventas?limite=2")
                segunda = await cliente.get("/api/ventas?limite=2&desplazamiento=2")
        finally:
            app.dependency_overrides.clear()

        assert primera.status_code == 200
        assert segunda.status_code == 200
        assert len(primera.json()) == 2
        assert len(segunda.json()) == 1
        # `fecha` solo difiere para la venta retrasada: las otras dos comparten
        # el mismo `now()` de la transacción y su orden relativo no es
        # determinista (`id` es `gen_random_uuid()`), así que se comparan como
        # conjunto. Lo determinista es que la retrasada quede en la última
        # página (fecha DESC) y las otras dos en la primera.
        assert {v["folio"] for v in primera.json()} == set(folios) - {folios[0]}
        assert [v["folio"] for v in segunda.json()] == [folios[0]]
        assert primera.json()[0]["lineas"][0]["producto_nombre"] == "Shampoo 400ml"

    async def test_padre_puede_registrar_y_consultar_ventas(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)

        registro = await _post_venta(
            sesion_de_pruebas,
            "padre",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 1)]},
        )
        assert registro.status_code == 201

        simular_rol(sesion_de_pruebas, "padre", usuario_de_pruebas)
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                consulta = await cliente.get("/api/ventas")
        finally:
            app.dependency_overrides.clear()

        assert consulta.status_code == 200
        assert len(consulta.json()) == 1

    async def test_descuento_mayor_al_subtotal_devuelve_422(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)

        respuesta = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [_linea(producto_id, 2)], "descuento": "200.00"},
        )

        assert respuesta.status_code == 422