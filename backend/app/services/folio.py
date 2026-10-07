from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def generar_folio(sesion: AsyncSession) -> str:
    """Folio `F-AAAA-NNNN` de la próxima venta (P22).

    Se llama **dentro de la transacción de la venta y antes del INSERT**. Toma
    un `pg_advisory_xact_lock` sobre una clave fija del año en curso: el lock
    se libera cuando termina la transacción completa del request (el commit
    de `get_db_session`), de modo que dos ventas simultáneas del mismo año
    quedan serializadas. El `UNIQUE` de `venta.folio` sigue siendo la red de
    seguridad si algo más llegara a colisionar.

    El año se toma de `now()` de la transacción, para que el folio coincida
    siempre con la `fecha` que quedará grabada en la venta.
    """
    anio = (
        await sesion.execute(text("SELECT EXTRACT(YEAR FROM now())::int"))
    ).scalar_one()
    await sesion.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:clave)::bigint)"),
        {"clave": f"folio-{anio}"},
    )
    ultimo_secuencial = (
        await sesion.execute(
            text(
                """
                SELECT COALESCE(MAX((split_part(folio, '-', 3))::int), 0)
                FROM venta
                WHERE folio LIKE :prefijo
                """
            ),
            {"prefijo": f"F-{anio}-%"},
        )
    ).scalar_one()
    return f"F-{anio}-{ultimo_secuencial + 1:04d}"