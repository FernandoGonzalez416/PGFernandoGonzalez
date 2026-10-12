import { useContext } from 'react'
import { ContextoOffline, type EstadoOffline } from './contexto'

export function useOffline(): EstadoOffline {
  const valor = useContext(ContextoOffline)
  if (!valor) throw new Error('useOffline debe usarse dentro de ProveedorOffline.')
  return valor
}
