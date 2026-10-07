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


async def _crear_usuario(sesion: AsyncSession, rol: str = "padre") -> UUID:
    auth_id = uuid4()
    await sesion.execute(
        text("INSERT INTO auth.users (id) VALUES (:auth_id)"),
        {"auth_id": auth_id},
    )
    return (
        await sesion.execute(
            text(
                """
                INSERT INTO usuario (auth_id, nombre, email, rol)
                VALUES (:auth_id, :nombre, :email, :rol)
                RETURNING id
                """
            ),
            {
                "auth_id": auth_id,
                "nombre": "Usuario B",
                "email": f"{uuid4().hex}@test.invalid",
                "rol": rol,
            },
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
            nombre="Rimel 12ml",
            categoria_id=await _crear_categoria(sesion),
            precio_venta=precio_venta,
            precio_costo=Decimal("20.00"),
            umbral_minimo=Decimal("5.00"),
            cantidad_inicial=cantidad_inicial,
        ),
        usuario_id,
    )
    return producto.id


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


async def _anular(
    sesion: AsyncSession,
    rol: str,
    usuario_id: UUID,
    venta_id: str,
    motivo: str,
) -> httpx2.Response:
    simular_rol(sesion, rol, usuario_id)
    try:
        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app),
            base_url="http://pruebas",
        ) as cliente:
            return await cliente.post(
                f"/api/ventas/{venta_id}/anular",
                json={"motivo_anulacion": motivo},
            )
    finally:
        app.dependency_overrides.clear()


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


class TestAnulacionDeVenta:
    async def test_anulacion_restaura_stock_y_deja_movimiento_entrada(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
        venta = await _post_venta(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            {"lineas": [{"producto_id": str(producto_id), "cantidad": 3}]},
        )
        venta_id = venta.json()["id"]
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("7.00")

        anulacion = await _anular(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            venta_id,
            "Cliente devolvió el artículo",
        )

        assert anulacion.status_code == 200
        cuerpo = anulacion.json()
        assert cuerpo["estado"] == "anulada"
        assert cuerpo["motivo_anulacion"] == "Cliente devolvió el artículo"
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("10.00")
        movimientos = await _movimientos(sesion_de_pruebas, producto_id)
        assert len(movimientos) == 3
        anulacion = next(
            m for m in movimientos if m["nota"].startswith("Anulación")
        )
        assert anulacion["tipo"] == "entrada"
        assert anulacion["referencia_tipo"] == "venta"
        assert anulacion["cantidad"] == 3
        assert "Cliente devolvió el artículo" in anulacion["nota"]

    async def test_anulacion_sin_motivo_devuelve_422(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
        venta_id = (
            await _post_venta(
                sesion_de_pruebas,
                "propietario",
                usuario_de_pruebas,
                {"lineas": [{"producto_id": str(producto_id), "cantidad": 1}]},
            )
        ).json()["id"]

        simular_rol(sesion_de_pruebas, "propietario", usuario_de_pruebas)
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.post(
                    f"/api/ventas/{venta_id}/anular",
                    json={"motivo_anulacion": "   "},
                )
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 422

    async def test_anulacion_repetida_devuelve_409(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto_id = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
        venta_id = (
            await _post_venta(
                sesion_de_pruebas,
                "propietario",
                usuario_de_pruebas,
                {"lineas": [{"producto_id": str(producto_id), "cantidad": 2}]},
            )
        ).json()["id"]

        primera = await _anular(
            sesion_de_pruebas, "propietario", usuario_de_pruebas, venta_id, "Motivo A"
        )
        segunda = await _anular(
            sesion_de_pruebas, "propietario", usuario_de_pruebas, venta_id, "Motivo B"
        )

        assert primera.status_code == 200
        assert segunda.status_code == 409
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("10.00")
        movimientos = await _movimientos(sesion_de_pruebas, producto_id)
        assert len(movimientos) == 3
        anulaciones = [
            m for m in movimientos if m["nota"].startswith("Anulación")
        ]
        assert len(anulaciones) == 1
        assert anulaciones[0]["cantidad"] == 2

    async def test_padre_no_puede_anular_venta_de_otro_usuario(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        dueno = usuario_de_pruebas
        padre = await _crear_usuario(sesion_de_pruebas, rol="padre")
        producto_id = await _crear_producto(sesion_de_pruebas, dueno)
        venta_id = (
            await _post_venta(
                sesion_de_pruebas,
                "propietario",
                dueno,
                {"lineas": [{"producto_id": str(producto_id), "cantidad": 3}]},
            )
        ).json()["id"]

        respuesta = await _anular(
            sesion_de_pruebas, "padre", padre, venta_id, "Cambió de opinión"
        )

        assert respuesta.status_code == 403
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("7.00")
        estados = (
            await sesion_de_pruebas.execute(
                text(
                    "SELECT estado FROM venta "
                    f"WHERE id = '{venta_id}'"
                )
            )
        ).scalar_one()
        assert estados == "activa"

    async def test_padre_anula_su_propia_venta(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        padre = await _crear_usuario(sesion_de_pruebas, rol="padre")
        producto_id = await _crear_producto(sesion_de_pruebas, padre)
        venta_id = (
            await _post_venta(
                sesion_de_pruebas,
                "padre",
                padre,
                {"lineas": [{"producto_id": str(producto_id), "cantidad": 2}]},
            )
        ).json()["id"]

        anulacion = await _anular(
            sesion_de_pruebas, "padre", padre, venta_id, "Venta fallida"
        )

        assert anulacion.status_code == 200
        assert anulacion.json()["estado"] == "anulada"
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("10.00")

    async def test_administrador_anula_cualquier_venta(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        administrador = usuario_de_pruebas
        padre = await _crear_usuario(sesion_de_pruebas, rol="padre")
        producto_id = await _crear_producto(sesion_de_pruebas, administrador)
        venta_id = (
            await _post_venta(
                sesion_de_pruebas,
                "padre",
                padre,
                {"lineas": [{"producto_id": str(producto_id), "cantidad": 4}]},
            )
        ).json()["id"]

        anulacion = await _anular(
            sesion_de_pruebas,
            "administrador",
            administrador,
            venta_id,
            "Prueba",
        )

        assert anulacion.status_code == 200
        assert anulacion.json()["estado"] == "anulada"
        assert await _cantidad(sesion_de_pruebas, producto_id) == Decimal("10.00")

    async def test_movimiento_compensatorio_por_cada_linea(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        primero = await _crear_producto(sesion_de_pruebas, usuario_de_pruebas)
        segundo = await _crear_producto(
            sesion_de_pruebas, usuario_de_pruebas, precio_venta=Decimal("80.00")
        )
        venta_id = (
            await _post_venta(
                sesion_de_pruebas,
                "propietario",
                usuario_de_pruebas,
                {
                    "lineas": [
                        {"producto_id": str(primero), "cantidad": 2},
                        {"producto_id": str(segundo), "cantidad": 1},
                    ]
                },
            )
        ).json()["id"]

        anulacion = await _anular(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            venta_id,
            "Devolución",
        )

        assert anulacion.status_code == 200
        assert await _cantidad(sesion_de_pruebas, primero) == Decimal("10.00")
        assert await _cantidad(sesion_de_pruebas, segundo) == Decimal("10.00")
        assert len(await _movimientos(sesion_de_pruebas, primero)) == 3
        assert len(await _movimientos(sesion_de_pruebas, segundo)) == 3
        for producto_id, cantidad in ((primero, 2), (segundo, 1)):
            movimientos = await _movimientos(sesion_de_pruebas, producto_id)
            anulacion = next(
                m for m in movimientos if m["nota"].startswith("Anulación")
            )
            assert anulacion["tipo"] == "entrada"
            assert anulacion["cantidad"] == cantidad

    async def test_anular_venta_inexistente_devuelve_404(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        respuesta = await _anular(
            sesion_de_pruebas,
            "propietario",
            usuario_de_pruebas,
            str(uuid4()),
            "Prueba",
        )

        assert respuesta.status_code == 404