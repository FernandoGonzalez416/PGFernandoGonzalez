from pydantic import BaseModel, Field


class MeRead(BaseModel):
    """Perfil del usuario autenticado más sus capacidades efectivas (P14).

    `capacidades` se deriva del rol en el backend para que el frontend no
    reimplemente la matriz de permisos: la interfaz solo pregunta si puede o no
    hacer algo, y el backend sigue siendo la autoridad final.
    """

    id: str
    auth_id: str
    nombre: str
    email: str
    rol: str
    activo: bool
    capacidades: list[str] = Field(
        description="Capacidades habilitadas para el rol, según P14."
    )
