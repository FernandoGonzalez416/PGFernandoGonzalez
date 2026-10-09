import type { Capacidad } from '../api/types'
import { useAuth } from './useAuth'

export function useCan(capacidad: Capacidad): boolean {
  const { perfil } = useAuth()
  return perfil?.capacidades.includes(capacidad) ?? false
}
