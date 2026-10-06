from fastapi import FastAPI

from app.api.me import router as me_router
from app.core import config

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="API principal: inventarios, ventas, alertas, reportes y predicción.",
)

app.include_router(me_router)


@app.get("/")
def root():
    return {"mensaje": config.APP_NAME, "version": config.APP_VERSION}


@app.get("/health")
def health():
    return {"status": "ok", "entorno": config.APP_ENV}