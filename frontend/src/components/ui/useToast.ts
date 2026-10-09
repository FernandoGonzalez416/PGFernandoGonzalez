import { useContext } from 'react'
import { ContextoToast, type ContextoToastValor } from './contextoToast'

export function useToast(): ContextoToastValor {
  const valor = useContext(ContextoToast)
  if (!valor) throw new Error('useToast debe usarse dentro de ToastProvider.')
  return valor
}
