from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errores import ProveedorNoEncontradoError
from app.schemas.proveedor import ProveedorCreate, ProveedorUpdate
from app.services import proveedores as servicio

pytestmark = pytest.mark.integracion


class TestCrear:
    async def test_crea_con_todos_los_datos(self, sesion_de_pruebas: AsyncSession) -> None:
        proveedor = await servicio.crear_proveedor(
            sesion_de_pruebas,
            ProveedorCreate(
                nombre="Distribuidora Centro",
                contacto="Ana López",
                telefono="5555-0101",
                email="ana@test.invalid",
                condiciones_entrega="Entrega en 48 horas",
                precio_habitual=Decimal("25.50"),
            ),
        )

        assert proveedor.nombre == "Distribuidora Centro"
        assert proveedor.contacto == "Ana López"
        assert proveedor.email == "ana@test.invalid"
        assert proveedor.precio_habitual == Decimal("25.50")
        assert proveedor.activo is True

    async def test_el_precio_se_cuantiza(self, sesion_de_pruebas: AsyncSession) -> None:
        proveedor = await servicio.crear_proveedor(
            sesion_de_pruebas,
            ProveedorCreate(nombre="Precios", precio_habitual=Decimal("10.005")),
        )

        assert proveedor.precio_habitual == Decimal("10.01")

    async def test_precio_habitual_es_opcional(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        proveedor = await servicio.crear_proveedor(
            sesion_de_pruebas, ProveedorCreate(nombre="Sin precio")
        )

        assert proveedor.precio_habitual is None

    async def test_el_nombre_no_tiene_restriccion_de_unicidad(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        """El plan solo declara UNIQUE en `categoria`; dos proveedores homónimos
        son legítimos (el mismo distribuidor puede facturar en varias sucursales)."""
        primero = await servicio.crear_proveedor(
            sesion_de_pruebas, ProveedorCreate(nombre="Homónimo")
        )
        segundo = await servicio.crear_proveedor(
            sesion_de_pruebas, ProveedorCreate(nombre="Homónimo")
        )

        assert primero.id != segundo.id


class TestListar:
    async def test_ordena_por_nombre(self, sesion_de_pruebas: AsyncSession) -> None:
        for nombre in ("Zeta", "Alfa", "Mid"):
            await servicio.crear_proveedor(
                sesion_de_pruebas, ProveedorCreate(nombre=f"{nombre}-{uuid4().hex[:6]}")
            )

        proveedores = await servicio.listar_proveedores(sesion_de_pruebas)

        assert [p.nombre for p in proveedores] == sorted(p.nombre for p in proveedores)

    async def test_los_inactivos_se_ocultan_por_defecto(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        activo = await servicio.crear_proveedor(
            sesion_de_pruebas, ProveedorCreate(nombre=f"Activo-{uuid4().hex[:6]}")
        )
        inactivo = await servicio.crear_proveedor(
            sesion_de_pruebas, ProveedorCreate(nombre=f"Inactivo-{uuid4().hex[:6]}")
        )
        await servicio.actualizar_proveedor(
            sesion_de_pruebas, inactivo.id, ProveedorUpdate(activo=False)
        )

        por_defecto = await servicio.listar_proveedores(sesion_de_pruebas)
        con_inactivos = await servicio.listar_proveedores(
            sesion_de_pruebas, incluir_inactivos=True
        )

        assert activo.id in {p.id for p in por_defecto}
        assert inactivo.id not in {p.id for p in por_defecto}
        assert inactivo.id in {p.id for p in con_inactivos}


class TestLeerYActualizar:
    async def test_obtener_inexistente(self, sesion_de_pruebas: AsyncSession) -> None:
        with pytest.raises(ProveedorNoEncontradoError):
            await servicio.obtener_proveedor(sesion_de_pruebas, uuid4())

    async def test_actualiza_precio_y_lo_cuantiza(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        proveedor = await servicio.crear_proveedor(
            sesion_de_pruebas, ProveedorCreate(nombre="Original")
        )

        actualizado = await servicio.actualizar_proveedor(
            sesion_de_pruebas, proveedor.id, ProveedorUpdate(precio_habitual=Decimal("33.335"))
        )

        assert actualizado.precio_habitual == Decimal("33.34")

    async def test_actualiza_condicion_de_entrega(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        proveedor = await servicio.crear_proveedor(
            sesion_de_pruebas, ProveedorCreate(nombre="Condiciones")
        )

        actualizado = await servicio.actualizar_proveedor(
            sesion_de_pruebas,
            proveedor.id,
            ProveedorUpdate(condiciones_entrega="Ahora 24 horas"),
        )

        assert actualizado.condiciones_entrega == "Ahora 24 horas"
        assert actualizado.nombre == "Condiciones"

    async def test_actualizar_sin_cambios_devuelve_el_mismo(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        proveedor = await servicio.crear_proveedor(
            sesion_de_pruebas, ProveedorCreate(nombre="Sin cambios")
        )

        resultado = await servicio.actualizar_proveedor(
            sesion_de_pruebas, proveedor.id, ProveedorUpdate()
        )

        assert resultado.nombre == "Sin cambios"

    async def test_actualizar_inexistente(self, sesion_de_pruebas: AsyncSession) -> None:
        with pytest.raises(ProveedorNoEncontradoError):
            await servicio.actualizar_proveedor(
                sesion_de_pruebas, uuid4(), ProveedorUpdate(nombre="X")
            )