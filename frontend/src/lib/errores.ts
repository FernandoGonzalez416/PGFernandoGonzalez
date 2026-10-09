import { ApiError } from '../api/client'

export function mensajeDeError(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error && error.message !== '') return error.message
  return 'Ocurrió un error inesperado. Intenta de nuevo.'
}
