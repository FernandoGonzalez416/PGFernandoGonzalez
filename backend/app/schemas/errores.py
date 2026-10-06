from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Envelope único de error de la API.

    El campo se llama `detail` porque es el contrato que ya consume `/api/me` y
    el que espera el frontend; no se cambia.
    """

    detail: str = Field(
        description="Mensaje accionable para la persona usuaria, sin detalles internos."
    )