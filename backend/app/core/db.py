from collections.abc import AsyncIterator
from functools import lru_cache
from typing import TypeAlias

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

SesionDB: TypeAlias = AsyncSession


@lru_cache
def get_engine():
    return create_async_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
    )


@lru_cache
def get_session_maker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Unidad de trabajo del request: confirma al salir, revierte ante error.

    La frontera transaccional es el request, no el servicio. Por eso los
    servicios se delimitan con `begin_nested()` (SAVEPOINT) y no con `begin()`:
    un SAVEPOINT revierte su propio tramo sin invalidar la sesion ni lo que el
    request ya habia escrito, y las pruebas de integracion (P20) conservan su
    transaccion exterior como frontera real del rollback.
    """
    async with get_session_maker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise