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

/**
 * Caché de lecturas (SWR mínima): las respuestas GET se reutilizan durante
 * `TTL_CACHE_MS` y las peticiones GET idénticas en vuelo comparten una sola
 * promesa. Así el doble montaje de StrictMode, reabrir la campana o volver a
 * una vista no disparan peticiones repetidas a Supabase. Cualquier escritura
 * (POST/PATCH/PUT/DELETE) invalida toda la caché.
 */
const TTL_CACHE_MS = 20_000

type EntradaCache = { expira: number; datos: unknown }

const cacheLecturas = new Map<string, EntradaCache>()
const peticionesEnVuelo = new Map<string, Promise<unknown>>()

export function limpiarCacheApi(): void {
  cacheLecturas.clear()
  peticionesEnVuelo.clear()
}

function clonarParaLectura<T>(datos: T): T {
  if (typeof structuredClone === 'function') return structuredClone(datos)
  return JSON.parse(JSON.stringify(datos)) as T
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

  const metodo = opciones.method?.toUpperCase() ?? 'GET'
  const url = `${API_URL}${ruta}`
  const esLectura = metodo === 'GET'
  const clave =
    esLectura ? `${metodo} ${url} ${token !== null && token !== '' ? token.slice(-12) : 'sin-token'}` : ''

  if (esLectura) {
    const entrada = cacheLecturas.get(clave)
    if (entrada !== undefined && entrada.expira > Date.now()) {
      return clonarParaLectura(entrada.datos as T)
    }
    const enVuelo = peticionesEnVuelo.get(clave)
    if (enVuelo !== undefined) {
      return clonarParaLectura((await enVuelo) as T)
    }
  }

  const peticion = (async (): Promise<T> => {
    let respuesta: Response
    try {
      respuesta = await fetch(url, { ...opciones, headers: cabeceras })
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
  })()

  if (!esLectura) {
    try {
      return await peticion
    } finally {
      limpiarCacheApi()
    }
  }

  peticionesEnVuelo.set(clave, peticion)
  try {
    const datos = await peticion
    cacheLecturas.set(clave, { expira: Date.now() + TTL_CACHE_MS, datos })
    return clonarParaLectura(datos)
  } finally {
    peticionesEnVuelo.delete(clave)
  }
}
