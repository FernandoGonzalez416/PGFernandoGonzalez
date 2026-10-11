from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.categorias import router as categorias_router
from app.api.inventario import router as inventario_router
from app.api.me import router as me_router
from app.api.predicciones import router as predicciones_router
from app.api.productos import router as productos_router
from app.api.proveedores import router as proveedores_router
from app.api.ventas import router as ventas_router
from app.api.alertas import router as alertas_router
from app.api.reportes import router as reportes_router
from app.api.sugerencias import router as sugerencias_router
from app.api.notificaciones import router as notificaciones_router
from app.core import config
from app.core.errores import (
    AnulacionNoPermitidaError,
    ClienteInvalidoError,
    ConflictoDeUnicidadError,
    DescuentoInvalidoError,
    EntidadNoEncontradaError,
    ErrorDeDominio,
    ProductoConExistenciasError,
    StockInsuficienteError,
    VencimientoInvalidoError,
    VentaNoAnulableError,
    AlertaNoEncontradaError,
    SugerenciaNoEncontradaError,
    SugerenciaNoPendienteError,
    NotificacionNoEncontradaError,
)
CODIGO_POR_ERROR: dict[type[ErrorDeDominio], int] = {
    EntidadNoEncontradaError: 404,
    ConflictoDeUnicidadError: 409,
    ProductoConExistenciasError: 409,
    StockInsuficienteError: 409,
    VencimientoInvalidoError: 422,
    ClienteInvalidoError: 422,
    DescuentoInvalidoError: 422,
    AnulacionNoPermitidaError: 403,
    VentaNoAnulableError: 409,
    SugerenciaNoPendienteError: 409,
}

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="API principal: inventarios, ventas, alertas, reportes y prediccion.",
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(me_router, prefix="/api", tags=["me"])
app.include_router(productos_router, prefix="/api/productos", tags=["productos"])
app.include_router(categorias_router, prefix="/api/categorias", tags=["categorias"])
app.include_router(proveedores_router, prefix="/api/proveedores", tags=["proveedores"])
app.include_router(inventario_router, prefix="/api/inventario", tags=["inventario"])
app.include_router(ventas_router, prefix="/api/ventas", tags=["ventas"])
app.include_router(alertas_router, prefix="/api/alertas", tags=["alertas"])
app.include_router(reportes_router, prefix="/api/reportes", tags=["reportes"])
app.include_router(sugerencias_router, prefix="/api/sugerencias", tags=["sugerencias"])
app.include_router(notificaciones_router, prefix="/api/notificaciones", tags=["notificaciones"])
app.include_router(predicciones_router, prefix="/api", tags=["predicciones"])


@app.get("/")
def root():
    return {"mensaje": config.APP_NAME, "version": config.APP_VERSION}


@app.get("/health")
def health():
    return {"status": "ok", "entorno": config.APP_ENV}
