from decimal import Decimal
from uuid import UUID, uuid4

import httpx2
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import simular_rol

from app.main import app
from app.schemas.existencia import ExistenciaAjuste
from app.schemas.producto import ProductoCreate
from app.services import existencia as servicio
from app.services import productos as servicio_productos

pytestmark = pytest.mark.integracion


async def _crear_categoria(sesion: AsyncSession) -> UUID:
    return (
        await sesion.execute(
            text(
                "INSERT INTO categoria (nombre) VALUES (:nombre) RETURNING id"
            ),
            {"nombre": f"Cat-{uuid4().hex[:8]}"},
        )
    ).scalar_one()


async def _crear_producto(
    sesion: AsyncSession, usuario_id: UUID, cantidad_inicial=Decimal("0")
) -> UUID:
    producto = await servicio_productos.crear_producto(
        sesion,
        ProductoCreate(
            codigo=f"P-{uuid4().hex[:8]}",
            nombre="Shampoo 400ml",
            categoria_id=await _crear_categoria(sesion),
            precio_venta=Decimal("55.00"),
            precio_costo=Decimal("32.00"),
            umbral_minimo=Decimal("5.00"),
            cantidad_inicial=cantidad_inicial,
        ),
        usuario_id,
    )
    return producto.id


async def _cantidad(sesion: AsyncSession, producto_id: UUID) -> Decimal | None:
    return (
        await sesion.execute(
            text(
                """
                SELECT cantidad FROM existencia
                WHERE producto_id = :producto_id
                """
            ),
            {"producto_id": producto_id},
        )
    ).scalar_one_or_none()


async def _movimientos(sesion: AsyncSession, producto_id: UUID) -> list[dict]:
    filas = (
        await sesion.execute(
            text(
                """
                SELECT tipo, referencia_tipo, cantidad, nota, usuario_id
                FROM movimiento_inventario
                WHERE producto_id = :producto_id
                ORDER BY fecha, id
                """
            ),
            {"producto_id": producto_id},
        )
    ).mappings().all()
    return [dict(fila) for fila in filas]


def _unico_ajuste(movimientos: list[dict]) -> dict:
    """El movimiento de ajuste, sin depender del orden de `fecha`.

    `now()` es el inicio de la transacción, así que el movimiento `inicial`
    y el del ajuste comparten fecha: ordenar por fecha no los separa.
    """
    ajustes = [m for m in movimientos if m["referencia_tipo"] == "ajuste"]
    assert len(ajustes) == 1, f"Se esperaba un solo ajuste y hay {len(ajustes)}"
    return ajustes[0]


async def _post_ajuste(
    sesion: AsyncSession, rol: str, usuario_id: UUID, cuerpo: dict
) -> httpx2.Response:
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app),
            base_url="http://pruebas",
        ) as cliente:
            return await cliente.post("/api/inventario/ajustes", json=cuerpo)
    finally:
        app.dependency_overrides.clear()


class TestAjusteDeStock:
    async def test_ajuste_positivo_suma_y_deja_movimiento_entrada(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("10.00")
        )

        respuesta = await _post_ajuste(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"producto_id": str(producto_id), "cantidad": "5.00", "nota": "Entrada por compra"},
        )

        assert respuesta.status_code == 201
        assert respuesta.json()["cantidad"] == "15.00"
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("15.00")

        movimientos = await _movimientos(sesion_de_pruebas, producto_id)
        assert len(movimientos) == 2
        ajuste = _unico_ajuste(movimientos)
        assert ajuste["tipo"] == "entrada"
        assert ajuste["referencia_tipo"] == "ajuste"
        assert ajuste["cantidad"] == Decimal("5.00")
        assert ajuste["nota"] == "Entrada por compra"
        assert ajuste["usuario_id"] == usuario_de_pruebas

    async def test_ajuste_negativo_resta_y_deja_movimiento_salida(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("10.00")
        )

        respuesta = await _post_ajuste(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"producto_id": str(producto_id), "cantidad": "-4.00", "nota": "Merma contada"},
        )

        assert respuesta.status_code == 201
        assert respuesta.json()["cantidad"] == "6.00"
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("6.00")

        movimientos = await _movimientos(sesion_de_pruebas, producto_id)
        ajuste = _unico_ajuste(movimientos)
        assert ajuste["tipo"] == "salida"
        assert ajuste["referencia_tipo"] == "ajuste"
        assert ajuste["cantidad"] == Decimal("4.00")

    async def test_ajuste_que_dejaria_stock_negativo_devuelve_409_sin_rastro(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("10.00")
        )
        previos = await _movimientos(sesion_de_pruebas, producto_id)

        respuesta = await _post_ajuste(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"producto_id": str(producto_id), "cantidad": "-15.00", "nota": "No cabe"},
        )

        assert respuesta.status_code == 409
        detalle = respuesta.json()["detail"]
        assert "Shampoo 400ml" in detalle
        assert "10.00" in detalle
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("10.00")
        assert await _movimientos(sesion_de_pruebas, producto_id) == previos

    async def test_ajuste_con_nota_vacia_devuelve_422(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("10.00")
        )

        respuesta = await _post_ajuste(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"producto_id": str(producto_id), "cantidad": "1.00", "nota": "   "},
        )

        assert respuesta.status_code == 422
        errores = respuesta.json()["detail"]
        assert any("nota" in str(detalle["loc"]) for detalle in errores)
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("10.00")

    async def test_ajuste_cero_devuelve_422(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("10.00")
        )

        respuesta = await _post_ajuste(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"producto_id": str(producto_id), "cantidad": "0.00", "nota": "Sin cambios"},
        )

        assert respuesta.status_code == 422
        errores = respuesta.json()["detail"]
        assert any("cantidad" in str(detalle["loc"]) for detalle in errores)

    async def test_ajuste_crea_la_existencia_si_no_existe(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        """El `upsert` cubre a un producto que quedó sin fila de existencia.

        El alta siempre crea la fila (regla de Fase A), así que el estado sin
        fila solo puede venir de datos heredados: se simula borrándola a mano.
        """
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("0")
        )
        await sesion_de_pruebas.execute(
            text("DELETE FROM existencia WHERE producto_id = :producto_id"),
            {"producto_id": producto_id},
        )
        assert await _cantidad(sesion_de_pruebas, producto_id) is None

        respuesta = await _post_ajuste(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"producto_id": str(producto_id), "cantidad": "5.00", "nota": "Primer conteo"},
        )

        assert respuesta.status_code == 201
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("5.00")
        movimientos = await _movimientos(sesion_de_pruebas, producto_id)
        assert len(movimientos) == 1
        assert movimientos[0]["tipo"] == "entrada"

    async def test_ajuste_a_producto_inexistente_devuelve_404(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        respuesta = await _post_ajuste(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"producto_id": str(uuid4()), "cantidad": "5.00", "nota": "No existe"},
        )

        assert respuesta.status_code == 404

    async def test_ajuste_con_campo_no_declarado_devuelve_422(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("10.00")
        )

        respuesta = await _post_ajuste(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {
                "producto_id": str(producto_id),
                "cantidad": "5.00",
                "nota": "Con almacén explícito",
                "almacen_id": str(uuid4()),
            },
        )

        assert respuesta.status_code == 422
        errores = respuesta.json()["detail"]
        assert any("almacen_id" in str(detalle["loc"]) for detalle in errores)
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("10.00")

    async def test_el_servicio_y_el_schema_coinciden_en_el_delta(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("10.00")
        )

        await servicio.ajustar_existencia(
            sesion_de_pruebas,
            ExistenciaAjuste(
                producto_id=producto_id, cantidad=Decimal("-2.5"), nota="Merma parcial"
            ),
            usuario_de_pruebas,
        )

        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("7.50")


class TestPermisosDeInventario:
    async def test_padre_no_puede_ajustar(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("10.00")
        )
        previos = await _movimientos(sesion_de_pruebas, producto_id)

        respuesta = await _post_ajuste(
            sesion_de_pruebas,
            "padre",
            usuario_de_pruebas,
            {"producto_id": str(producto_id), "cantidad": "1.00", "nota": "No permitido"},
        )

        assert respuesta.status_code == 403
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("10.00")
        assert await _movimientos(sesion_de_pruebas, producto_id) == previos

    async def test_padre_si_puede_ver_existencia(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("7.00")
        )
        simular_rol(sesion_de_pruebas, "padre", usuario_de_pruebas)
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.get(
                    f"/api/inventario/existencia?producto_id={producto_id}"
                )
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert len(cuerpo) == 1
        assert cuerpo[0]["cantidad"] == "7.00"
        assert cuerpo[0]["almacen_nombre"] == almacen_de_pruebas

    async def test_padre_si_puede_ver_movimientos(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("3.00")
        )
        simular_rol(sesion_de_pruebas, "padre", usuario_de_pruebas)
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.get(
                    f"/api/inventario/movimientos?producto_id={producto_id}"
                )
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert len(cuerpo) == 1
        assert cuerpo[0]["tipo"] == "entrada"
        assert cuerpo[0]["referencia_tipo"] == "inicial"
        assert cuerpo[0]["cantidad"] == "3.00"


class TestListadoDeMovimientos:
    async def test_listado_paginado_respeta_limite_y_desplazamiento(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("0")
        )
        almacen_id = (
            await sesion_de_pruebas.execute(
                text("SELECT id FROM almacen WHERE nombre = :nombre"),
                {"nombre": almacen_de_pruebas},
            )
        ).scalar_one()

        for dias_atras, cantidad in ((3, "13.00"), (2, "23.00"), (1, "33.00")):
            await sesion_de_pruebas.execute(
                text(
                    """
                    INSERT INTO movimiento_inventario (
                        producto_id, almacen_id, tipo, referencia_tipo,
                        cantidad, usuario_id, nota, fecha
                    )
                    VALUES (
                        :producto_id, :almacen_id, 'entrada', 'ajuste',
                        :cantidad, :usuario_id, :nota,
                        now() - make_interval(days => :dias_atras)
                    )
                    """
                ),
                {
                    "producto_id": producto_id,
                    "almacen_id": almacen_id,
                    "cantidad": cantidad,
                    "usuario_id": usuario_de_pruebas,
                    "nota": f"dia-{dias_atras}",
                    "dias_atras": dias_atras,
                },
            )

        simular_rol(sesion_de_pruebas, "propietario", usuario_de_pruebas)
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                primera = await cliente.get(
                    "/api/inventario/movimientos"
                    f"?producto_id={producto_id}&limite=2"
                )
                segunda = await cliente.get(
                    "/api/inventario/movimientos"
                    f"?producto_id={producto_id}&limite=2&desplazamiento=2"
                )
        finally:
            app.dependency_overrides.clear()

        assert primera.status_code == 200
        assert segunda.status_code == 200
        assert [item["nota"] for item in primera.json()] == ["dia-1", "dia-2"]
        assert [item["nota"] for item in segunda.json()] == ["dia-3"]
        assert [item["cantidad"] for item in segunda.json()] == ["13.00"]


class TestListadoDeExistencia:
    async def test_producto_con_cantidad_cero_sigue_apareciendo_en_el_listado(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        """Un artículo recién dado de alta sin entradas debe ser visible.

        Requerimiento funcional 3 (AGENTS.md): las alertas de bajo stock
        necesitan ver la existencia en 0.00, que es justo el caso que más
        atención requiere.
        """
        producto_id = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, Decimal("0")
        )

        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("0.00")

        simular_rol(sesion_de_pruebas, "propietario", usuario_de_pruebas)
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.get("/api/inventario/existencia")
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 200
        filas = [
            fila
            for fila in respuesta.json()
            if fila["producto_id"] == str(producto_id)
        ]
        assert len(filas) == 1, "El producto en cero no aparece en el listado"
        assert filas[0]["cantidad"] == "0.00"
