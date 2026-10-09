from fastapi import APIRouter, Depends

from app.core.capacidades import capacidades_de_rol
from app.core.security import UsuarioAutenticado, get_current_usuario
from app.schemas.me import MeRead

router = APIRouter()


@router.get("/me")
async def leer_usuario_actual(
    usuario: UsuarioAutenticado = Depends(get_current_usuario),
) -> MeRead:
    return MeRead(**usuario.model_dump(), capacidades=capacidades_de_rol(usuario.rol))
