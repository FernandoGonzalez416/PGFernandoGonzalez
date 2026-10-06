from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import httpx2
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import simular_rol

from app.core.errores import (
    CategoriaNoEncontradaError,
    CodigoProductoDuplicadoError,
    ProductoConExistenciasError,
    ProductoNoEncontradoError,
    ProveedorNoEncontradoError,
    VencimientoInvalidoError,
)
from app.main import app
from app.schemas.producto import ProductoCreate, ProductoUpdate
from app.services import productos as servicio

pytestmark = pytest.mark.integracion


async def _crear_categoria(sesion: AsyncSession, nombre: str | None = None) -> UUID:
    # `uq_categoria_nombre` es UNIQUE: cada alta necesita su propia categoría.
    nombre = nombre or f"Cat-{uuid4().hex[:8]}"
    return (
        await sesion.execute(
            text("INSERT INTO categoria (nombre) VALUES (:nombre) RETURNING id"),
            {"nombre": nombre},
        )
    ).scalar_one()


async def _crear_proveedor(sesion: AsyncSession, nombre: str = "Distribuidor") -> UUID:
    return (
        await sesion.execute(
            text("INSERT INTO proveedor (nombre) VALUES (:nombre) RETURNING id"),
            {"nombre": nombre},
        )
    ).scalar_one()


async def _datos(
    sesion: AsyncSession, **cambios
) -> ProductoCreate:
    base = {
        "codigo": f"P-{uuid4().hex[:8]}",
        "nombre": "Shampoo 400ml",
        "categoria_id": await _crear_categoria(sesion),
        "precio_venta": Decimal("55.00"),
        "precio_costo": Decimal("32.00"),
        "umbral_minimo": Decimal("5.00"),
    }
    base.update(cambios)
    return ProductoCreate(**base)


async def _contar_movimientos(sesion: AsyncSession, producto_id: UUID) -> int:
    return (
        await sesion.execute(
            text("SELECT count(*) FROM movimiento_inventario WHERE producto_id = :id"),
            {"id": producto_id},
        )
    ).scalar_one()


async def _crear(
    sesion: AsyncSession,
    usuario_id: UUID,
    almacen_de_pruebas: str,
    **cambios,
):
    return await servicio.crear_producto(
        sesion, await _datos(sesion, **cambios), usuario_id
    )


class TestAltaDeProducto:
    async def test_alta_deja_movimiento_inicial(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            cantidad_inicial=Decimal("24.00"),
        )

        assert producto.existencia == Decimal("24.00")
        assert await _contar_movimientos(sesion_de_pruebas, producto.id) == 1

        movimiento = (
            await sesion_de_pruebas.execute(
                text(
                    """
                    SELECT tipo, referencia_tipo, referencia_id, cantidad, nota, usuario_id
                    FROM movimiento_inventario WHERE producto_id = :id
                    """
                ),
                {"id": producto.id},
            )
        ).mappings().one()
        assert movimiento["tipo"] == "entrada"
        assert movimiento["referencia_tipo"] == "inicial"
        assert movimiento["referencia_id"] == producto.id
        assert movimiento["cantidad"] == Decimal("24.00")
        assert movimiento["nota"] == "Alta de producto"
        assert movimiento["usuario_id"] == usuario_de_pruebas

    async def test_cantidad_cero_no_crea_movimiento(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            cantidad_inicial=Decimal("0"),
        )

        assert producto.existencia == Decimal("0.00")
        assert await _contar_movimientos(sesion_de_pruebas, producto.id) == 0

        cantidad_en_almacen = (
            await sesion_de_pruebas.execute(
                text(
                    """
                    SELECT cantidad FROM existencia
                    WHERE producto_id = :producto_id
                    """
                ),
                {"producto_id": producto.id},
            )
        ).scalar_one_or_none()
        assert cantidad_en_almacen == Decimal("0.00"), (
            "La fila de existencia debe crearse siempre, también en cero"
        )

    async def test_la_existencia_queda_en_el_almacen_por_defecto(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        await sesion_de_pruebas.execute(
            text("INSERT INTO almacen (nombre) VALUES ('Sucursal')")
        )
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            cantidad_inicial=Decimal("10.00"),
        )

        existencias = await servicio.listar_existencias(
            sesion_de_pruebas, producto.id
        )
        assert len(existencias) == 1
        assert existencias[0].almacen_nombre == almacen_de_pruebas
        assert existencias[0].cantidad == Decimal("10.00")

    async def test_acepta_el_usuario_como_texto(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        """`UsuarioAutenticado.id` llega como texto; no debe romperse."""
        producto = await servicio.crear_producto(
            sesion_de_pruebas,
            await _datos(sesion_de_pruebas, cantidad_inicial=Decimal("2.00")),
            str(usuario_de_pruebas),
        )

        assert producto.existencia == Decimal("2.00")


class TestCodigoDuplicado:
    async def test_codigo_duplicado_409(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        await _crear(sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas, codigo="P-DUP")

        with pytest.raises(CodigoProductoDuplicadoError):
            await _crear(
                sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas, codigo="P-DUP"
            )

    async def test_el_rechazo_no_deja_producto_ni_movimiento(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            codigo="P-DUP2",
            cantidad_inicial=Decimal("3.00"),
        )

        with pytest.raises(CodigoProductoDuplicadoError):
            await _crear(
                sesion_de_pruebas,
                usuario_de_pruebas,
                almacen_de_pruebas,
                codigo="P-DUP2",
                cantidad_inicial=Decimal("99.00"),
            )

        total_productos = (
            await sesion_de_pruebas.execute(
                text("SELECT count(*) FROM producto WHERE codigo = 'P-DUP2'")
            )
        ).scalar_one()
        total_movimientos = (
            await sesion_de_pruebas.execute(
                text(
                    """
                    SELECT count(*) FROM movimiento_inventario m
                    JOIN producto p ON p.id = m.producto_id
                    WHERE p.codigo = 'P-DUP2'
                    """
                )
            )
        ).scalar_one()
        assert total_productos == 1
        assert total_movimientos == 1

    async def test_la_existencia_no_se_incrementa_al_rechazar(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            codigo="P-DUP3",
            cantidad_inicial=Decimal("5.00"),
        )

        with pytest.raises(CodigoProductoDuplicadoError):
            await _crear(
                sesion_de_pruebas,
                usuario_de_pruebas,
                almacen_de_pruebas,
                codigo="P-DUP3",
                cantidad_inicial=Decimal("500.00"),
            )

        total_existencia = (
            await sesion_de_pruebas.execute(
                text(
                    """
                    SELECT COALESCE(sum(cantidad), 0) FROM existencia e
                    JOIN producto p ON p.id = e.producto_id
                    WHERE p.codigo = 'P-DUP3'
                    """
                )
            )
        ).scalar_one()
        assert total_existencia == Decimal("5.00")


class TestVencimiento:
    async def test_vencimiento_en_pasado_se_rechaza(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        datos = await _datos(
            sesion_de_pruebas, fecha_vencimiento=date.today() - timedelta(days=1)
        )

        with pytest.raises(VencimientoInvalidoError):
            await servicio.crear_producto(sesion_de_pruebas, datos, usuario_de_pruebas)

    async def test_no_persiste_el_producto_rechazado(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        with pytest.raises(VencimientoInvalidoError):
            await _crear(
                sesion_de_pruebas,
                usuario_de_pruebas,
                almacen_de_pruebas,
                codigo="P-VENCIDO",
                cantidad_inicial=Decimal("4.00"),
                fecha_vencimiento=date.today() - timedelta(days=5),
            )

        total = (
            await sesion_de_pruebas.execute(
                text("SELECT count(*) FROM producto WHERE codigo = 'P-VENCIDO'")
            )
        ).scalar_one()
        assert total == 0

    async def test_vencimiento_hoy_si_se_acepta(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            fecha_vencimiento=date.today(),
        )

        assert producto.fecha_vencimiento == date.today()

    async def test_sin_vencimiento_es_no_perecedero(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas
        )

        assert producto.fecha_vencimiento is None

    async def test_actualizar_vencimiento_al_pasado_se_rechaza(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas
        )

        with pytest.raises(VencimientoInvalidoError):
            await servicio.actualizar_producto(
                sesion_de_pruebas,
                producto.id,
                ProductoUpdate(fecha_vencimiento=date.today() - timedelta(days=1)),
            )


class TestReferenciasInvalidas:
    async def test_categoria_inexistente(
        self, sesion_de_pruebas: AsyncSession, almacen_de_pruebas: str
    ) -> None:
        datos = ProductoCreate(
            codigo="P-SIN-CAT",
            nombre="Sin categoría",
            categoria_id=uuid4(),
            precio_venta=Decimal("10.00"),
            precio_costo=Decimal("5.00"),
        )

        with pytest.raises(CategoriaNoEncontradaError):
            await servicio.crear_producto(
                sesion_de_pruebas, datos, uuid4()
            )

    async def test_proveedor_inexistente(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        with pytest.raises(ProveedorNoEncontradoError):
            await _crear(
                sesion_de_pruebas,
                usuario_de_pruebas,
                almacen_de_pruebas,
                proveedor_id=uuid4(),
            )

    async def test_proveedor_valido_se_asigna(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        proveedor_id = await _crear_proveedor(sesion_de_pruebas)

        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            proveedor_id=proveedor_id,
        )

        assert producto.proveedor_id == proveedor_id


class TestPrecios:
    async def test_los_precios_se_cuantizan(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            precio_venta=Decimal("55.005"),
            precio_costo=Decimal("32.004"),
            umbral_minimo=Decimal("5.005"),
        )

        assert producto.precio_venta == Decimal("55.01")
        assert producto.precio_costo == Decimal("32.00")
        assert producto.umbral_minimo == Decimal("5.01")

    async def test_el_precio_cuantizado_se_persiste(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            precio_venta=Decimal("99.99"),
        )

        guardado = (
            await sesion_de_pruebas.execute(
                text("SELECT precio_venta FROM producto WHERE id = :id"),
                {"id": producto.id},
            )
        ).scalar_one()
        assert guardado == Decimal("99.99")

    async def test_actualizar_precio_lo_cuantiza(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas
        )

        actualizado = await servicio.actualizar_producto(
            sesion_de_pruebas, producto.id, ProductoUpdate(precio_venta=Decimal("70.005"))
        )

        assert actualizado.precio_venta == Decimal("70.01")


class TestDesactivar:
    async def test_con_existencias_se_rechaza(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            cantidad_inicial=Decimal("7.00"),
        )

        with pytest.raises(ProductoConExistenciasError):
            await servicio.actualizar_producto(
                sesion_de_pruebas, producto.id, ProductoUpdate(activo=False)
            )

    async def test_el_rechazo_no_lo_desactiva(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            cantidad_inicial=Decimal("7.00"),
        )

        with pytest.raises(ProductoConExistenciasError):
            await servicio.actualizar_producto(
                sesion_de_pruebas, producto.id, ProductoUpdate(activo=False)
            )

        assert (await servicio.obtener_producto(sesion_de_pruebas, producto.id)).activo

    async def test_sin_stock_si_se_puede_desactivar(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            cantidad_inicial=Decimal("0"),
        )

        actualizado = await servicio.actualizar_producto(
            sesion_de_pruebas, producto.id, ProductoUpdate(activo=False)
        )

        assert actualizado.activo is False

    async def test_con_ventas_activas_se_rechaza(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            cantidad_inicial=Decimal("0"),
        )
        venta_id = (
            await sesion_de_pruebas.execute(
                text(
                    """
                    INSERT INTO venta (folio, usuario_id, metodo_pago, subtotal, total)
                    VALUES ('F-2026-0001', :usuario_id, 'efectivo', 100, 100)
                    RETURNING id
                    """
                ),
                {"usuario_id": usuario_de_pruebas},
            )
        ).scalar_one()
        await sesion_de_pruebas.execute(
            text(
                """
                INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (:venta_id, :producto_id, 1, 100, 100)
                """
            ),
            {"venta_id": venta_id, "producto_id": producto.id},
        )

        with pytest.raises(ProductoConExistenciasError):
            await servicio.actualizar_producto(
                sesion_de_pruebas, producto.id, ProductoUpdate(activo=False)
            )

    async def test_una_venta_anulada_no_impide_desactivar(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            cantidad_inicial=Decimal("0"),
        )
        venta_id = (
            await sesion_de_pruebas.execute(
                text(
                    """
                    INSERT INTO venta (
                        folio, usuario_id, metodo_pago, subtotal, total,
                        estado, motivo_anulacion
                    )
                    VALUES ('F-2026-0002', :usuario_id, 'efectivo', 100, 100,
                            'anulada', 'Prueba')
                    RETURNING id
                    """
                ),
                {"usuario_id": usuario_de_pruebas},
            )
        ).scalar_one()
        await sesion_de_pruebas.execute(
            text(
                """
                INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (:venta_id, :producto_id, 1, 100, 100)
                """
            ),
            {"venta_id": venta_id, "producto_id": producto.id},
        )

        actualizado = await servicio.actualizar_producto(
            sesion_de_pruebas, producto.id, ProductoUpdate(activo=False)
        )

        assert actualizado.activo is False


class TestLeerYActualizar:
    async def test_obtener_inexistente(
        self, sesion_de_pruebas: AsyncSession, almacen_de_pruebas: str
    ) -> None:
        with pytest.raises(ProductoNoEncontradoError):
            await servicio.obtener_producto(sesion_de_pruebas, uuid4())

    async def test_actualizar_inexistente(
        self, sesion_de_pruebas: AsyncSession, almacen_de_pruebas: str
    ) -> None:
        with pytest.raises(ProductoNoEncontradoError):
            await servicio.actualizar_producto(
                sesion_de_pruebas, uuid4(), ProductoUpdate(nombre="Nuevo")
            )

    async def test_listar_existencias_de_inexistente(
        self, sesion_de_pruebas: AsyncSession, almacen_de_pruebas: str
    ) -> None:
        with pytest.raises(ProductoNoEncontradoError):
            await servicio.listar_existencias(sesion_de_pruebas, uuid4())

    async def test_actualizar_nombre_no_toca_el_codigo(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            codigo="P-FIJO",
        )

        actualizado = await servicio.actualizar_producto(
            sesion_de_pruebas, producto.id, ProductoUpdate(nombre="Shampoo nuevo")
        )

        assert actualizado.nombre == "Shampoo nuevo"
        assert actualizado.codigo == "P-FIJO"


class TestPermisosDelPadre:
    """Contraste directo de P14: el padre consulta, pero no escribe.

    Se usa `httpx2.AsyncClient` y no `TestClient` a propósito: `TestClient` corre
    la app en su propio event loop y una conexión asyncpg no puede compartirse
    entre loops. Con el cliente async la app y la sesión de la prueba comparten
    loop, y así se conserva la verificación HTTP y el rollback de P20.
    """

    async def test_padre_si_puede_consultar(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            nombre="Shampoo de prueba",
        )
        simular_rol(sesion_de_pruebas, "padre")
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.get("/api/productos?q=Shampoo")
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert [item["id"] for item in cuerpo] == [str(producto.id)]
        assert cuerpo[0]["existencia"] == "0.00"

    async def test_padre_no_puede_crear(
        self,
        sesion_de_pruebas: AsyncSession,
        almacen_de_pruebas: str,
    ) -> None:
        categoria_id = await _crear_categoria(sesion_de_pruebas)
        simular_rol(sesion_de_pruebas, "padre")
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.post(
                    "/api/productos",
                    json={
                        "codigo": "P-PADRE",
                        "nombre": "No debe crearse",
                        "categoria_id": str(categoria_id),
                        "precio_venta": "10.00",
                        "precio_costo": "5.00",
                    },
                )
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 403
        total = (
            await sesion_de_pruebas.execute(
                text("SELECT count(*) FROM producto WHERE codigo = 'P-PADRE'")
            )
        ).scalar_one()
        assert total == 0


class TestCamposNoEditables:
    """Un campo no declarado en `ProductoUpdate` debe rechazarse con 422.

    Con `extra="forbid"` el PATCH con `codigo` (inmutable) deja de devolver un
    200 silencioso que descartaba el campo: ahora el error es explícito.
    """

    async def test_patch_producto_con_campo_no_editable_devuelve_422(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await _crear(
            sesion_de_pruebas,
            usuario_de_pruebas,
            almacen_de_pruebas,
            nombre="Producto con codigo fijo",
        )
        simular_rol(sesion_de_pruebas, "propietario")
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.patch(
                    f"/api/productos/{producto.id}",
                    json={"codigo": "ALGO"},
                )
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 422
        errores = respuesta.json()["detail"]
        assert any("codigo" in str(detalle["loc"]) for detalle in errores)
        # El nombre no se tocó: el rechazo ocurre antes de tocar la base.
        assert (
            await servicio.obtener_producto(sesion_de_pruebas, producto.id)
        ).nombre == "Producto con codigo fijo"


class TestCamposNoCreables:
    """Un campo no declarado en `ProductoCreate` se rechaza con 422.

    Mismo criterio que `TestCamposNoEditables`, pero sobre el POST de alta:
    `existencia` pertenece a `ProductoRead` (se calcula a partir del almacén),
    no a la creación, así que un cliente que la envíe recibe un error explícito
    en vez de un 201 engañoso.
    """

    async def test_post_producto_con_campo_no_creado_devuelve_422(
        self,
        sesion_de_pruebas: AsyncSession,
        almacen_de_pruebas: str,
    ) -> None:
        categoria_id = await _crear_categoria(sesion_de_pruebas)
        simular_rol(sesion_de_pruebas, "propietario")
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.post(
                    "/api/productos",
                    json={
                        "codigo": "P-EXTRA",
                        "nombre": "No debe crearse",
                        "categoria_id": str(categoria_id),
                        "precio_venta": "10.00",
                        "precio_costo": "5.00",
                        "existencia": "99.00",
                    },
                )
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 422
        errores = respuesta.json()["detail"]
        assert any("existencia" in str(detalle["loc"]) for detalle in errores)
        total = (
            await sesion_de_pruebas.execute(
                text("SELECT count(*) FROM producto WHERE codigo = 'P-EXTRA'")
            )
        ).scalar_one()
        assert total == 0
