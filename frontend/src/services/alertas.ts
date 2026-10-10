import { apiFetch } from '../api/client'
import type { AlertaResumen } from '../api/types'

export function listarAlertas(): Promise<AlertaResumen> {
  return apiFetch<AlertaResumen>('/api/alertas/')
}