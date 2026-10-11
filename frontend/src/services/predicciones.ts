import { apiFetch } from '../api/client'
import type { PrediccionRead, SerieResponse } from '../api/types'

export function listarPredicciones(): Promise<PrediccionRead[]> {
  return apiFetch<PrediccionRead[]>('/api/predicciones')
}

export function obtenerSeriePrediccion(productoId: string): Promise<SerieResponse> {
  return apiFetch<SerieResponse>(`/api/predicciones/${productoId}/serie`)
}