from fastapi import APIRouter, Depends

from app.core.security import UsuarioAutenticado, get_current_usuario

router = APIRouter()


@router.get("/api/me")
async def leer_usuario_actual(
    usuario: UsuarioAutenticado = Depends(get_current_usuario),
) -> UsuarioAutenticado:
    return usuario
