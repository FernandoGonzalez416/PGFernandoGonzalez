from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.producto import ProductoCreate, ProductoUpdate
from app.services import productos as servicio

pytestmark = pytest.mark.integracion


async def _crear_categoria(sesion: AsyncSession) -> UUID:
    # `uq_categoria_nombre` es UNIQUE: cada alta necesita su propia categoría.
    return (
        await sesion.execute(
            text("INSERT INTO categoria (nombre) VALUES (:n) RETURNING id"),
            {"n": f"Cat-{uuid4().hex[:8]}"},
        )
    ).scalar_one()


async def _producto(
    sesion: AsyncSession,
    *,
    nombre: str = "Shampoo 400ml",
    codigo: str | None = None,
    categoria_id: UUID | None = None,
    cantidad: Decimal = Decimal("0"),
) -> ProductoCreate:
    return ProductoCreate(
        codigo=codigo or f"P-{uuid4().hex[:8]}",
        nombre=nombre,
        categoria_id=categoria_id or await _crear_categoria(sesion),
        precio_venta=Decimal("55.00"),
        precio_costo=Decimal("32.00"),
        cantidad_inicial=cantidad,
    )


async def _sembrar(
    sesion: AsyncSession, usuario_id: UUID, almacen_de_pruebas: str
) -> list:
    """Alta de varios productos representativos para buscar."""
    creados = []
    for nombre, codigo, cantidad in (
        ("Shampoo 400ml", "SH-400", Decimal("12.00")),
        ("Shampoo Hydra", "SH-500", Decimal("3.00")),
        ("Acondicionador 400ml", "AC-400", Decimal("8.00")),
        ("Tintura rubia", "TI-100", Decimal("0")),
    ):
        creados.append(
            await servicio.crear_producto(
                sesion,
                await _producto(
                    sesion,
                    nombre=nombre,
                    codigo=codigo,
                    cantidad=cantidad,
                ),
                usuario_id,
            )
        )
    return creados


class TestBusquedaPorNombre:
    async def test_encuentra_por_nombre_sin_distincion_de_mayusculas(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        await _sembrar(sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas)

        resultados = await servicio.listar_productos(sesion_de_pruebas, q="shampoo")

        assert {p.nombre for p in resultados} == {
            "Shampoo 400ml",
            "Shampoo Hydra",
        }

    async def test_encuentra_por_texto_parcial(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        await _sembrar(sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas)

        resultados = await servicio.listar_productos(sesion_de_pruebas, q="400ml")

        assert {p.nombre for p in resultados} == {
            "Shampoo 400ml",
            "Acondicionador 400ml",
        }

    async def test_sin_coincidencias_devuelve_lista_vacia(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        await _sembrar(sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas)

        resultados = await servicio.listar_productos(
            sesion_de_pruebas, q="inexistente-zzz"
        )

        assert resultados == []


class TestBusquedaPorCodigo:
    async def test_encuentra_por_codigo_exacto(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        await _sembrar(sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas)

        resultados = await servicio.listar_productos(sesion_de_pruebas, q="TI-100")

        assert [p.nombre for p in resultados] == ["Tintura rubia"]

    async def test_el_codigo_no_se_busca_de_forma_parcial(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        """El plan pide coincidencia EXACTA de `codigo` (regla 5 de Fase A)."""
        await _sembrar(sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas)

        resultados = await servicio.listar_productos(sesion_de_pruebas, q="SH-")

        assert resultados == []


class TestBusquedaPorCategoria:
    async def test_filtra_por_categoria(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        categoria_id = await _crear_categoria(sesion_de_pruebas)
        en_categoria = await servicio.crear_producto(
            sesion_de_pruebas,
            ProductoCreate(
                codigo=f"P-{uuid4().hex[:8]}",
                nombre="En la categoría",
                categoria_id=categoria_id,
                precio_venta=Decimal("10.00"),
                precio_costo=Decimal("5.00"),
            ),
            usuario_de_pruebas,
        )
        await servicio.crear_producto(
            sesion_de_pruebas,
            await _producto(sesion_de_pruebas, nombre="Fuera"),
            usuario_de_pruebas,
        )

        resultados = await servicio.listar_productos(
            sesion_de_pruebas, categoria_id=categoria_id
        )

        assert [p.id for p in resultados] == [en_categoria.id]


class TestFiltrosCombinables:
    async def test_nombre_y_categoria_se_combinan(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        categoria_shampoo = await _crear_categoria(sesion_de_pruebas)
        otra_categoria = await _crear_categoria(sesion_de_pruebas)
        dentro = await servicio.crear_producto(
            sesion_de_pruebas,
            ProductoCreate(
                codigo=f"P-{uuid4().hex[:8]}",
                nombre="Shampoo de la categoría",
                categoria_id=categoria_shampoo,
                precio_venta=Decimal("10.00"),
                precio_costo=Decimal("5.00"),
            ),
            usuario_de_pruebas,
        )
        await servicio.crear_producto(
            sesion_de_pruebas,
            ProductoCreate(
                codigo=f"P-{uuid4().hex[:8]}",
                nombre="Shampoo de otra categoría",
                categoria_id=otra_categoria,
                precio_venta=Decimal("10.00"),
                precio_costo=Decimal("5.00"),
            ),
            usuario_de_pruebas,
        )

        resultados = await servicio.listar_productos(
            sesion_de_pruebas, q="Shampoo", categoria_id=categoria_shampoo
        )

        assert [p.id for p in resultados] == [dentro.id]


class TestInactivosYOrden:
    async def test_los_inactivos_no_aparecen_por_defecto(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        producto = await servicio.crear_producto(
            sesion_de_pruebas,
            await _producto(sesion_de_pruebas, nombre="Para ocultar"),
            usuario_de_pruebas,
        )
        await servicio.actualizar_producto(
            sesion_de_pruebas, producto.id, ProductoUpdate(activo=False)
        )

        visibles = await servicio.listar_productos(
            sesion_de_pruebas, q="Para ocultar"
        )
        con_inactivos = await servicio.listar_productos(
            sesion_de_pruebas, q="Para ocultar", incluir_inactivos=True
        )

        assert visibles == []
        assert [p.id for p in con_inactivos] == [producto.id]

    async def test_orden_por_nombre(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        for nombre in ("Zeta", "Alfa", "Mid"):
            await servicio.crear_producto(
                sesion_de_pruebas,
                await _producto(sesion_de_pruebas, nombre=nombre),
                usuario_de_pruebas,
            )

        resultados = await servicio.listar_productos(sesion_de_pruebas)

        assert [p.nombre for p in resultados] == ["Alfa", "Mid", "Zeta"]


class TestExistenciaEnLaRespuesta:
    async def test_devuelve_la_cantidad_por_defecto(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        await _sembrar(sesion_de_pruebas, usuario_de_pruebas, almacen_de_pruebas)

        resultados = await servicio.listar_productos(sesion_de_pruebas, q="SH-400")

        assert resultados[0].existencia == Decimal("12.00")

    async def test_sin_existencia_devuelve_cero_con_dos_decimales(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        """Un producto sin fila en `existencia` debe reportar `0.00`, no `0`."""
        producto = await servicio.crear_producto(
            sesion_de_pruebas,
            await _producto(sesion_de_pruebas, nombre="Sin stock"),
            usuario_de_pruebas,
        )

        assert producto.existencia == Decimal("0.00")


class TestPaginacion:
    async def test_respeta_el_limite(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        for indice in range(5):
            await servicio.crear_producto(
                sesion_de_pruebas,
                await _producto(sesion_de_pruebas,
                    nombre=f"Producto {indice}",
                ),
                usuario_de_pruebas,
            )

        resultados = await servicio.listar_productos(sesion_de_pruebas, limite=2)

        assert [p.nombre for p in resultados] == ["Producto 0", "Producto 1"]

    async def test_el_desplazamiento_continua_la_paginacion(
        self,
        sesion_de_pruebas: AsyncSession,
        usuario_de_pruebas: UUID,
        almacen_de_pruebas: str,
    ) -> None:
        for indice in range(3):
            await servicio.crear_producto(
                sesion_de_pruebas,
                await _producto(sesion_de_pruebas,
                    nombre=f"Item {indice}",
                ),
                usuario_de_pruebas,
            )

        resultados = await servicio.listar_productos(
            sesion_de_pruebas, limite=2, desplazamiento=2
        )

        assert [p.nombre for p in resultados] == ["Item 2"]