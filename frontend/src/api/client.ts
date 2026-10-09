import { API_URL } from '../lib/env'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
  }
}

type ConfiguracionAutenticacion = {
  obtenerToken: () => Promise<string | null>
  alExpirarSesion: () => void | Promise<void>
}

let obtenerToken: () => Promise<string | null> = async () => null
let alExpirarSesion: () => void | Promise<void> = () => {}

export function configurarAutenticacion(configuracion: ConfiguracionAutenticacion): void {
  obtenerToken = configuracion.obtenerToken
  alExpirarSesion = configuracion.alExpirarSesion
}

function esObjeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === 'object' && valor !== null
}

function esDetalleTexto(cuerpo: unknown): cuerpo is { detail: string } {
  return esObjeto(cuerpo) && typeof cuerpo['detail'] === 'string'
}

function esDetalleValidacion(cuerpo: unknown): cuerpo is { detail: unknown[] } {
  return esObjeto(cuerpo) && Array.isArray(cuerpo['detail'])
}

function mensajePorEstado(status: number): string {
  if (status === 401) return 'Tu sesión expiró. Vuelve a iniciar sesión.'
  if (status === 403) return 'No tienes permiso para realizar esta acción.'
  if (status === 404) return 'No se encontró lo que buscabas.'
  if (status === 409) return 'La operación no se pudo completar por un conflicto con los datos.'
  if (status === 422) return 'Revisa los datos ingresados.'
  if (status >= 500) return 'Ocurrió un error en el servidor. Intenta de nuevo en un momento.'
  return 'No se pudo completar la solicitud.'
}

function mensajeDeValidacion(cuerpo: { detail: unknown[] }): string | null {
  const primero = cuerpo.detail[0]
  if (!esObjeto(primero)) return null
  const mensaje = primero['msg']
  const ubicacion = primero['loc']
  const campo = Array.isArray(ubicacion) ? ubicacion[ubicacion.length - 1] : undefined
  if (campo !== undefined && campo !== 'body') {
    return `El valor de «${String(campo)}» no es válido.`
  }
  return typeof mensaje === 'string' ? 'Revisa los datos ingresados.' : null
}

async function extraerMensaje(respuesta: Response): Promise<string> {
  let cuerpo: unknown
  try {
    cuerpo = await respuesta.json()
  } catch {
    cuerpo = null
  }
  if (esDetalleTexto(cuerpo) && cuerpo.detail.trim() !== '') return cuerpo.detail
  if (esDetalleValidacion(cuerpo)) {
    const mensaje = mensajeDeValidacion(cuerpo)
    if (mensaje) return mensaje
  }
  return mensajePorEstado(respuesta.status)
}

export async function apiFetch<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const token = await obtenerToken()
  const cabeceras = new Headers(opciones.headers)
  if (opciones.body !== undefined && opciones.body !== null && !cabeceras.has('Content-Type')) {
    cabeceras.set('Content-Type', 'application/json')
  }
  if (token !== null && token !== '') cabeceras.set('Authorization', `Bearer ${token}`)

  let respuesta: Response
  try {
    respuesta = await fetch(`${API_URL}${ruta}`, { ...opciones, headers: cabeceras })
  } catch {
    throw new ApiError(0, 'No se pudo conectar con el servidor. Revisa tu conexión e intenta de nuevo.')
  }

  if (respuesta.status === 401) {
    await alExpirarSesion()
    throw new ApiError(401, mensajePorEstado(401))
  }

  if (!respuesta.ok) {
    throw new ApiError(respuesta.status, await extraerMensaje(respuesta))
  }

  if (respuesta.status === 204) return undefined as T

  const datos: unknown = await respuesta.json()
  return datos as T
}
