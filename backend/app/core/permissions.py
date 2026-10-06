from fastapi import Depends, HTTPException, status

from app.core.capacidades import CAPACIDADES_POR_ROL, Capacidad
from app.core.security import UsuarioAutenticado, get_current_usuario


def requiere(capacidad: Capacidad):
    def dependencia(
        usuario: UsuarioAutenticado = Depends(get_current_usuario),
    ) -> UsuarioAutenticado:
        if usuario.rol not in CAPACIDADES_POR_ROL[capacidad]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El rol '{usuario.rol}' no tiene la capacidad '{capacidad.value}'",
            )
        return usuario
    return dependencia