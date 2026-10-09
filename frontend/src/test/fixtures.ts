import type { MeRead } from '../api/types'

export function crearPerfil(rol: string, capacidades: string[]): MeRead {
  return {
    id: 'usuario-1',
    auth_id: 'auth-1',
    nombre: 'Usuario de prueba',
    email: 'prueba@correo.com',
    rol,
    activo: true,
    capacidades,
  }
}
