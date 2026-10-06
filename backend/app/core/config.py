import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_NAME: str = "Plataforma de inventarios y reabastecimiento"
    APP_VERSION: str = "0.1.0"
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    ALMACEN_PREDETERMINADO: str = os.getenv("ALMACEN_PREDETERMINADO", "Principal")


settings = Settings()

APP_ENV = settings.APP_ENV
APP_NAME = settings.APP_NAME
APP_VERSION = settings.APP_VERSION
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_ANON_KEY = settings.SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL = settings.DATABASE_URL
ALMACEN_PREDETERMINADO = settings.ALMACEN_PREDETERMINADO