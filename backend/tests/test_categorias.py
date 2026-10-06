from uuid import uuid4

import httpx2
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import simular_rol

from app.core.errores import CategoriaDuplicadaError, CategoriaNoEncontradaError
from app.main import app
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate
from app.services import categorias as servicio

pytestmark = pytest.mark.integracion


class TestCrear:
    async def test_crea_con_nombre_y_descripcion(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        categoria = await servicio.crear_categoria(
            sesion_de_pruebas,
            CategoriaCreate(nombre="Perfumería", descripcion="Fragrancias"),
        )

        assert categoria.nombre == "Perfumería"
        assert categoria.descripcion == "Fragrancias"
        assert categoria.activo is True

    async def test_nombre_duplicado_no_se_permite(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre="Maquillaje")
        )

        with pytest.raises(CategoriaDuplicadaError):
            await servicio.crear_categoria(
                sesion_de_pruebas, CategoriaCreate(nombre="Maquillaje")
            )

    async def test_el_nombre_duplicado_difiere_solo_en_mayusculas(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        """La unicidad es sobre `lower(nombre)`, no sobre el texto exacto."""
        await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre="Cuidado facial")
        )

        with pytest.raises(CategoriaDuplicadaError):
            await servicio.crear_categoria(
                sesion_de_pruebas, CategoriaCreate(nombre="CUIDADO FACIAL")
            )

    async def test_no_deja_categoria_al_rechazar(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre="Cuidado corporal")
        )

        with pytest.raises(CategoriaDuplicadaError):
            await servicio.crear_categoria(
                sesion_de_pruebas, CategoriaCreate(nombre="cuidado corporal")
            )

        total = await servicio.listar_categorias(
            sesion_de_pruebas, incluir_inactivas=True
        )
        assert len([c for c in total if c.nombre.lower() == "cuidado corporal"]) == 1


class TestListar:
    async def test_ordena_por_nombre(self, sesion_de_pruebas: AsyncSession) -> None:
        for nombre in ("Zapatos", "Accesorios", "Medias"):
            await servicio.crear_categoria(
                sesion_de_pruebas, CategoriaCreate(nombre=f"{nombre}-{uuid4().hex[:6]}")
            )

        categorias = await servicio.listar_categorias(sesion_de_pruebas)

        assert [c.nombre for c in categorias] == sorted(c.nombre for c in categorias)

    async def test_las_inactivas_se_ocultan_por_defecto(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        visible = await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre=f"Visible-{uuid4().hex[:6]}")
        )
        oculta = await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre=f"Oculta-{uuid4().hex[:6]}")
        )
        await servicio.actualizar_categoria(
            sesion_de_pruebas, oculta.id, CategoriaUpdate(activo=False)
        )

        por_defecto = await servicio.listar_categorias(sesion_de_pruebas)
        con_inactivas = await servicio.listar_categorias(
            sesion_de_pruebas, incluir_inactivas=True
        )

        assert visible.id in {c.id for c in por_defecto}
        assert oculta.id not in {c.id for c in por_defecto}
        assert oculta.id in {c.id for c in con_inactivas}


class TestActualizar:
    async def test_cambia_el_nombre(self, sesion_de_pruebas: AsyncSession) -> None:
        categoria = await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre=f"Viejo-{uuid4().hex[:6]}")
        )

        actualizada = await servicio.actualizar_categoria(
            sesion_de_pruebas, categoria.id, CategoriaUpdate(nombre="Nuevo nombre")
        )

        assert actualizada.nombre == "Nuevo nombre"

    async def test_rechaza_nombre_duplicado(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre="Ocupado")
        )
        otra = await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre="Libre")
        )

        with pytest.raises(CategoriaDuplicadaError):
            await servicio.actualizar_categoria(
                sesion_de_pruebas, otra.id, CategoriaUpdate(nombre="Ocupado")
            )

    async def test_no_cambia_el_nombre_al_rechazar(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre="Ocupado2")
        )
        otra = await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre="Libre2")
        )

        with pytest.raises(CategoriaDuplicadaError):
            await servicio.actualizar_categoria(
                sesion_de_pruebas, otra.id, CategoriaUpdate(nombre="Ocupado2")
            )

        assert (await servicio.obtener_categoria(sesion_de_pruebas, otra.id)).nombre == (
            "Libre2"
        )

    async def test_inexistente(self, sesion_de_pruebas: AsyncSession) -> None:
        with pytest.raises(CategoriaNoEncontradaError):
            await servicio.actualizar_categoria(
                sesion_de_pruebas, uuid4(), CategoriaUpdate(nombre="X")
            )
class TestCamposNoEditables:
    """Un campo no declarado en `CategoriaUpdate` se rechaza con 422.

    Mismo criterio que `test_productos.py::TestCamposNoEditables`: con
    `extra="forbid"` el PATCH deja de devolver un 200 silencioso que descartaba
    el campo.
    """

    async def test_patch_categoria_con_campo_no_editable_devuelve_422(
        self, sesion_de_pruebas: AsyncSession
    ) -> None:
        categoria = await servicio.crear_categoria(
            sesion_de_pruebas, CategoriaCreate(nombre=f"Con id fijo-{uuid4().hex[:6]}")
        )
        simular_rol(sesion_de_pruebas, "propietario")
        try:
            async with httpx2.AsyncClient(
                transport=httpx2.ASGITransport(app=app),
                base_url="http://pruebas",
            ) as cliente:
                respuesta = await cliente.patch(
                    f"/api/categorias/{categoria.id}",
                    json={"id": str(categoria.id)},
                )
        finally:
            app.dependency_overrides.clear()

        assert respuesta.status_code == 422
        errores = respuesta.json()["detail"]
        assert any("id" in str(detalle["loc"]) for detalle in errores)
        assert (
            await servicio.obtener_categoria(sesion_de_pruebas, categoria.id)
        ).nombre == categoria.nombre
