from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dinero import a_cuantia
from app.core.errores import ProveedorNoEncontradoError
from app.schemas.proveedor import ProveedorCreate, ProveedorRead, ProveedorUpdate

CAMPOS = (
    "id, nombre, contacto, telefono, email, condiciones_entrega, "
    "precio_habitual, activo, created_at, updated_at"
)


async def listar_proveedores(
    sesion: AsyncSession, incluir_inactivos: bool = False
) -> list[ProveedorRead]:
    filas = (
        await sesion.execute(
            text(
                f"""
                SELECT {CAMPOS}
                FROM proveedor
                WHERE (:incluir_inactivos OR activo = true)
                ORDER BY nombre
                """
            ),
            {"incluir_inactivos": incluir_inactivos},
        )
    ).mappings().all()
    return [ProveedorRead(**dict(fila)) for fila in filas]


async def obtener_proveedor(sesion: AsyncSession, proveedor_id: UUID) -> ProveedorRead:
    fila = (
        await sesion.execute(
            text(f"SELECT {CAMPOS} FROM proveedor WHERE id = :proveedor_id"),
            {"proveedor_id": proveedor_id},
        )
    ).mappings().first()
    if fila is None:
        raise ProveedorNoEncontradoError(str(proveedor_id))
    return ProveedorRead(**dict(fila))


async def crear_proveedor(
    sesion: AsyncSession, datos: ProveedorCreate
) -> ProveedorRead:
    datos = datos.cuantizado()
    async with sesion.begin_nested():
        fila = (
            await sesion.execute(
                text(
                    f"""
                    INSERT INTO proveedor (
                        nombre, contacto, telefono, email,
                        condiciones_entrega, precio_habitual
                    )
                    VALUES (
                        :nombre, :contacto, :telefono, :email,
                        :condiciones_entrega, :precio_habitual
                    )
                    RETURNING {CAMPOS}
                    """
                ),
                {
                    "nombre": datos.nombre,
                    "contacto": datos.contacto,
                    "telefono": datos.telefono,
                    "email": datos.email,
                    "condiciones_entrega": datos.condiciones_entrega,
                    "precio_habitual": datos.precio_habitual,
                },
            )
        ).mappings().one()
        return ProveedorRead(**dict(fila))


async def actualizar_proveedor(
    sesion: AsyncSession, proveedor_id: UUID, datos: ProveedorUpdate
) -> ProveedorRead:
    async with sesion.begin_nested():
        await obtener_proveedor(sesion, proveedor_id)

        campos = {
            clave: valor
            for clave, valor in datos.model_dump(exclude_unset=True).items()
            if valor is not None
        }
        if "precio_habitual" in campos:
            campos["precio_habitual"] = a_cuantia(campos["precio_habitual"])

        if campos:
            asignaciones = ", ".join(f"{clave} = :{clave}" for clave in campos)
            fila = (
                await sesion.execute(
                    text(
                        f"""
                        UPDATE proveedor SET {asignaciones}
                        WHERE id = :proveedor_id
                        RETURNING {CAMPOS}
                        """
                    ),
                    {**campos, "proveedor_id": proveedor_id},
                )
            ).mappings().one()
            return ProveedorRead(**dict(fila))

    return await obtener_proveedor(sesion, proveedor_id)