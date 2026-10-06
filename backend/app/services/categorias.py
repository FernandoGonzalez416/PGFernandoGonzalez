from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errores import (
    CategoriaDuplicadaError,
    CategoriaNoEncontradaError,
    _menciona_restriccion,
)
from app.schemas.categoria import CategoriaCreate, CategoriaRead, CategoriaUpdate

RESTRICCION_NOMBRE_UNICO = "uq_categoria_nombre"

CAMPOS = "id, nombre, descripcion, activo, created_at, updated_at"


def _es_violacion_de_nombre(error: IntegrityError) -> bool:
    return _menciona_restriccion(error, RESTRICCION_NOMBRE_UNICO)


async def listar_categorias(
    sesion: AsyncSession, incluir_inactivas: bool = False
) -> list[CategoriaRead]:
    filas = (
        await sesion.execute(
            text(
                f"""
                SELECT {CAMPOS}
                FROM categoria
                WHERE (:incluir_inactivas OR activo = true)
                ORDER BY nombre
                """
            ),
            {"incluir_inactivas": incluir_inactivas},
        )
    ).mappings().all()
    return [CategoriaRead(**dict(fila)) for fila in filas]


async def obtener_categoria(sesion: AsyncSession, categoria_id: UUID) -> CategoriaRead:
    fila = (
        await sesion.execute(
            text(f"SELECT {CAMPOS} FROM categoria WHERE id = :categoria_id"),
            {"categoria_id": categoria_id},
        )
    ).mappings().first()
    if fila is None:
        raise CategoriaNoEncontradaError(str(categoria_id))
    return CategoriaRead(**dict(fila))


async def crear_categoria(sesion: AsyncSession, datos: CategoriaCreate) -> CategoriaRead:
    try:
        async with sesion.begin_nested():
            fila = (
                await sesion.execute(
                    text(
                        f"""
                        INSERT INTO categoria (nombre, descripcion)
                        VALUES (:nombre, :descripcion)
                        RETURNING {CAMPOS}
                        """
                    ),
                    {"nombre": datos.nombre, "descripcion": datos.descripcion},
                )
            ).mappings().one()
            return CategoriaRead(**dict(fila))
    except IntegrityError as error:
        if _es_violacion_de_nombre(error):
            raise CategoriaDuplicadaError(datos.nombre) from error
        raise


async def actualizar_categoria(
    sesion: AsyncSession, categoria_id: UUID, datos: CategoriaUpdate
) -> CategoriaRead:
    async with sesion.begin_nested():
        await obtener_categoria(sesion, categoria_id)

        campos = {
            clave: valor
            for clave, valor in datos.model_dump(exclude_unset=True).items()
            if valor is not None
        }
        if campos:
            try:
                asignaciones = ", ".join(f"{clave} = :{clave}" for clave in campos)
                fila = (
                    await sesion.execute(
                        text(
                            f"""
                            UPDATE categoria SET {asignaciones}
                            WHERE id = :categoria_id
                            RETURNING {CAMPOS}
                            """
                        ),
                        {**campos, "categoria_id": categoria_id},
                    )
                ).mappings().one()
            except IntegrityError as error:
                if _es_violacion_de_nombre(error):
                    raise CategoriaDuplicadaError(str(campos.get("nombre", ""))) from error
                raise
            return CategoriaRead(**dict(fila))

    return await obtener_categoria(sesion, categoria_id)