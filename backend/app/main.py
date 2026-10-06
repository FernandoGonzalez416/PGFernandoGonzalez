from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.categorias import router as categorias_router
from app.api.me import router as me_router
from app.api.productos import router as productos_router
from app.api.proveedores import router as proveedores_router
from app.core import config
from app.core.errores import (
    ConflictoDeUnicidadError,
    EntidadNoEncontradaError,
    ErrorDeDominio,
    ProductoConExistenciasError,
    VencimientoInvalidoError,
)

CODIGO_POR_ERROR: dict[type[ErrorDeDominio], int] = {
    EntidadNoEncontradaError: 404,
    ConflictoDeUnicidadError: 409,
    ProductoConExistenciasError: 409,
    VencimientoInvalidoError: 422,
}

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="API principal: inventarios, ventas, alertas, reportes y predicción.",
)


async def manejar_error_de_dominio(
    _request: Request,
    error: ErrorDeDominio,
) -> JSONResponse:
    codigo = CODIGO_POR_ERROR.get(type(error))
    if codigo is None:
        codigo = next(
            (
                valor
                for clase, valor in CODIGO_POR_ERROR.items()
                if isinstance(error, clase)
            ),
            500,
        )
    return JSONResponse(status_code=codigo, content={"detail": error.mensaje})


app.add_exception_handler(ErrorDeDominio, manejar_error_de_dominio)

app.include_router(me_router, prefix="/api", tags=["me"])
app.include_router(productos_router, prefix="/api/productos", tags=["productos"])
app.include_router(categorias_router, prefix="/api/categorias", tags=["categorias"])
app.include_router(proveedores_router, prefix="/api/proveedores", tags=["proveedores"])


@app.get("/")
def root():
    return {"mensaje": config.APP_NAME, "version": config.APP_VERSION}


@app.get("/health")
def health():
    return {"status": "ok", "entorno": config.APP_ENV}