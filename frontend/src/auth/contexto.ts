import { createContext } from 'react'
import type { MeRead } from '../api/types'

export type EstadoAutenticacion = {
  perfil: MeRead | null
  cargando: boolean
  iniciarSesion: (email: string, password: string) => Promise<void>
  cerrarSesion: () => Promise<void>
}

export const ContextoAutenticacion = createContext<EstadoAutenticacion | null>(null)
