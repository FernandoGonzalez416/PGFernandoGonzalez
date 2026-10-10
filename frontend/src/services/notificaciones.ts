import { apiFetch } from '../api/client'
import type { ListaConTotal, NotificacionItem } from '../api/types'

export type FiltrosNotificaciones = {
  leida?: boolean
  limite?: number
  desplazamiento?: number
}

function construirConsulta(filtros: FiltrosNotificaciones): string {
  const busqueda = new URLSearchParams()
  if (filtros.leida !== undefined) busqueda.set('leida', String(filtros.leida))
  if (filtros.limite !== undefined) busqueda.set('limite', String(filtros.limite))
  if (filtros.desplazamiento !== undefined) {
    busqueda.set('desplazamiento', String(filtros.desplazamiento))
  }
  const cadena = busqueda.toString()
  return cadena === '' ? '' : `?${cadena}`
}

export function listarNotificaciones(
  filtros: FiltrosNotificaciones = {},
): Promise<ListaConTotal<NotificacionItem>> {
  return apiFetch<ListaConTotal<NotificacionItem>>(`/api/notificaciones${construirConsulta(filtros)}`)
}

export function marcarNotificacionLeida(notificacionId: string): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>(`/api/notificaciones/${notificacionId}/leida`, {
    method: 'PATCH',
  })
}