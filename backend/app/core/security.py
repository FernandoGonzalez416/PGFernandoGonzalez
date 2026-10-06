from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db_session

bearer_scheme = HTTPBearer(auto_error=True)

# Margen para la diferencia de reloj entre Supabase Auth y este servidor.
# Sin el, un token emitido en los ultimos segundos se rechaza como "no valido todavia" (iat).
LEEWAY_SEGUNDOS = 30


@lru_cache
def get_jwks_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(
        f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json",
        cache_keys=True,
    )


class UsuarioAutenticado(BaseModel):
    id: str
    auth_id: str
    nombre: str
    email: str
    rol: str
    activo: bool


async def get_current_usuario(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> UsuarioAutenticado:
    token = credentials.credentials

    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        if alg not in ("ES256", "RS256"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Algoritmo de firma no soportado: {alg}",
            )
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[alg],
            audience="authenticated",
            leeway=LEEWAY_SEGUNDOS,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado, inicia sesión de nuevo",
        ) from exc

    auth_id = payload.get("sub")
    if not auth_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin sub")

    result = await db.execute(
        text("SELECT id, auth_id, nombre, email, rol, activo FROM usuario WHERE auth_id = :auth_id"),
        {"auth_id": auth_id},
    )
    row = result.mappings().first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sin perfil registrado")

    usuario = UsuarioAutenticado(
        id=str(row["id"]),
        auth_id=str(row["auth_id"]),
        nombre=row["nombre"],
        email=row["email"],
        rol=row["rol"],
        activo=row["activo"],
    )
    if not usuario.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
    return usuario