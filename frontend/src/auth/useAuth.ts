import { useContext } from 'react'
import { ContextoAutenticacion, type EstadoAutenticacion } from './contexto'

export function useAuth(): EstadoAutenticacion {
  const valor = useContext(ContextoAutenticacion)
  if (!valor) throw new Error('useAuth debe usarse dentro de ProveedorAutenticacion.')
  return valor
}
