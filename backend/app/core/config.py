import os

from dotenv import load_dotenv

load_dotenv()


def _a_bool(valor: str) -> bool:
    """Interpreta una variable de entorno booleana (P4).

    Solo los valores inequívocos encienden el flag; cualquier otra cosa
    (vacío, basura) deja el flag apagado, que es el estado seguro.
    """
    return valor.strip().lower() in {"1", "true", "yes", "si", "sí"}


def _a_entero(valor: str, por_defecto: int) -> int:
    """Interpreta una variable de entorno entera; ante basura usa el defecto."""
    try:
        numero = int(valor.strip())
    except (AttributeError, ValueError):
        return por_defecto
    return numero if numero > 0 else por_defecto


def _a_lista(valor: str) -> list[str]:
    """Separa una variable de entorno por comas, descartando elementos vacíos."""
    return [elemento.strip() for elemento in valor.split(",") if elemento.strip()]


ORIGENES_CORS_POR_DEFECTO = "http://localhost:5173,http://127.0.0.1:5173"


class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_NAME: str = "Plataforma de inventarios y reabastecimiento"
    APP_VERSION: str = "0.1.0"
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    ALMACEN_PREDETERMINADO: str = os.getenv("ALMACEN_PREDETERMINADO", "Principal")
    DATOS_FICTICIOS: bool = _a_bool(os.getenv("DATOS_FICTICIOS", "false"))
    CORS_ORIGINS: list[str] = _a_lista(
        os.getenv("CORS_ORIGINS", ORIGENES_CORS_POR_DEFECTO)
    )
    DB_POOL_SIZE: int = _a_entero(os.getenv("DB_POOL_SIZE", "10"), 10)
    DB_MAX_OVERFLOW: int = _a_entero(os.getenv("DB_MAX_OVERFLOW", "10"), 10)


settings = Settings()

APP_ENV = settings.APP_ENV
APP_NAME = settings.APP_NAME
APP_VERSION = settings.APP_VERSION
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_ANON_KEY = settings.SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL = settings.DATABASE_URL
ALMACEN_PREDETERMINADO = settings.ALMACEN_PREDETERMINADO
DATOS_FICTICIOS = settings.DATOS_FICTICIOS
CORS_ORIGINS = settings.CORS_ORIGINS
DB_POOL_SIZE = settings.DB_POOL_SIZE
DB_MAX_OVERFLOW = settings.DB_MAX_OVERFLOW