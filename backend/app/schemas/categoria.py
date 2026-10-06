from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoriaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str | None = None


class CategoriaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    descripcion: str | None = None
    activo: bool | None = None


class CategoriaRead(BaseModel):
    id: UUID
    nombre: str
    descripcion: str | None
    activo: bool
    created_at: datetime
    updated_at: datetime