import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errores import (
    CategoriaDuplicadaError,
    CategoriaNoEncontradaError,
    CodigoProductoDuplicadoError,
    ConflictoDeUnicidadError,
    EntidadNoEncontradaError,
    ErrorDeDominio,
    ProductoConExistenciasError,
    ProductoNoEncontradoError,
    ProveedorNoEncontradoError,
    VencimientoInvalidoError,
)
from app.main import manejar_error_de_dominio


def construir_cliente() -> TestClient:
    """App mínima que usa el manejador real de `app.main`."""
    app = FastAPI()
    app.add_exception_handler(ErrorDeDominio, manejar_error_de_dominio)

    @app.get("/error/{error}")
    def lanzar(error: str) -> None:
        errores: dict[str, ErrorDeDominio] = {
            "producto_no_encontrado": ProductoNoEncontradoError("abc"),
            "categoria_no_encontrada": CategoriaNoEncontradaError("abc"),
            "proveedor_no_encontrado": ProveedorNoEncontradoError("abc"),
            "codigo_duplicado": CodigoProductoDuplicadoError("P-1"),
            "categoria_duplicada": CategoriaDuplicadaError("Labiales"),
            "producto_con_existencias": ProductoConExistenciasError("tiene stock"),
            "vencimiento_invalido": VencimientoInvalidoError("venció ayer"),
        }
        raise errores[error]

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def cliente() -> TestClient:
    return construir_cliente()


@pytest.mark.parametrize(
    ("error", "codigo_esperado"),
    [
        ("producto_no_encontrado", 404),
        ("categoria_no_encontrada", 404),
        ("proveedor_no_encontrado", 404),
        ("codigo_duplicado", 409),
        ("categoria_duplicada", 409),
        ("producto_con_existencias", 409),
        ("vencimiento_invalido", 422),
    ],
)
def test_cada_error_de_dominio_traduce_a_su_codigo(
    cliente: TestClient, error: str, codigo_esperado: int
) -> None:
    respuesta = cliente.get(f"/error/{error}")
    assert respuesta.status_code == codigo_esperado


@pytest.mark.parametrize(
    "error",
    [
        "producto_no_encontrado",
        "categoria_no_encontrada",
        "proveedor_no_encontrado",
        "codigo_duplicado",
        "categoria_duplicada",
        "producto_con_existencias",
        "vencimiento_invalido",
    ],
)
def test_el_envelope_es_detail(cliente: TestClient, error: str) -> None:
    respuesta = cliente.get(f"/error/{error}")
    cuerpo = respuesta.json()
    assert list(cuerpo.keys()) == ["detail"]
    assert cuerpo["detail"]


def test_el_mensaje_llega_intacto(cliente: TestClient) -> None:
    respuesta = cliente.get("/error/codigo_duplicado")
    assert respuesta.json()["detail"] == "Ya existe un producto con el código 'P-1'"


def test_no_se_filtra_el_tipo_interno(cliente: TestClient) -> None:
    respuesta = cliente.get("/error/categoria_duplicada")
    assert "CategoriaDuplicadaError" not in respuesta.text
    assert "Traceback" not in respuesta.text


class TestJerarquia:
    def test_los_de_producto_heredan_de_entidad_no_encontrada(self) -> None:
        assert issubclass(ProductoNoEncontradoError, EntidadNoEncontradaError)

    def test_los_de_unicidad_heredan_del_conflicto(self) -> None:
        assert issubclass(CodigoProductoDuplicadoError, ConflictoDeUnicidadError)
        assert issubclass(CategoriaDuplicadaError, ConflictoDeUnicidadError)

    @pytest.mark.parametrize(
        "error",
        [
            ProductoNoEncontradoError("a"),
            CodigoProductoDuplicadoError("b"),
            ProductoConExistenciasError("c"),
            VencimientoInvalidoError("d"),
        ],
    )
    def test_todos_heredan_de_error_de_dominio(self, error: ErrorDeDominio) -> None:
        assert isinstance(error, ErrorDeDominio)