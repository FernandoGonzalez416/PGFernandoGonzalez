/**
 * Almacenamiento local versionado y separado por usuario (P27/F5).
 *
 * Características:
 * - Claves versionadas para permitir migraciones futuras.
 * - Separación por id de usuario para no mezclar colas entre usuarios.
 * - Manejo de errores con try/catch.
 * - Manejo de cuota llena con aviso claro (no se pierden datos silenciosamente).
 */

const PREFIJO_APP = 'pg_inventario_offline_'
const VERSION_ESQUEMA = 1

export type TipoDato = 'cola_ventas' | 'catalogo_cache' | 'estado_app'

function clave(tipo: TipoDato, usuarioId: string): string {
  return `${PREFIJO_APP}v${VERSION_ESQUEMA}_${tipo}_${usuarioId}`
}

export interface ResultadoGuardado {
  exito: boolean
  error?: string
}

export interface ResultadoLectura<T> {
  datos: T | null
  error?: string
}

/**
 * Guarda un dato en localStorage con manejo de errores.
 * Si la cuota está llena, devuelve un error claro.
 */
export function guardarDato<T>(tipo: TipoDato, usuarioId: string, datos: T): ResultadoGuardado {
  try {
    const claveCompleta = clave(tipo, usuarioId)
    const serializado = JSON.stringify(datos)
    localStorage.setItem(claveCompleta, serializado)
    return { exito: true }
  } catch (error) {
    if (error instanceof DOMException && error.name === 'QuotaExceededError') {
      return {
        exito: false,
        error: 'Almacenamiento lleno. Libera espacio en el navegador o reduce los datos pendientes.',
      }
    }
    return {
      exito: false,
      error: error instanceof Error ? error.message : 'Error desconocido al guardar.',
    }
  }
}

/**
 * Lee un dato de localStorage con manejo de errores.
 * Si el dato está corrupto o no existe, devuelve null.
 */
export function leerDato<T>(tipo: TipoDato, usuarioId: string): ResultadoLectura<T> {
  try {
    const claveCompleta = clave(tipo, usuarioId)
    const crudo = localStorage.getItem(claveCompleta)
    if (crudo === null) {
      return { datos: null }
    }
    const datos = JSON.parse(crudo) as T
    return { datos }
  } catch (error) {
    return {
      datos: null,
      error: error instanceof Error ? error.message : 'Error desconocido al leer.',
    }
  }
}

/**
 * Elimina un dato de localStorage.
 */
export function eliminarDato(tipo: TipoDato, usuarioId: string): ResultadoGuardado {
  try {
    const claveCompleta = clave(tipo, usuarioId)
    localStorage.removeItem(claveCompleta)
    return { exito: true }
  } catch (error) {
    return {
      exito: false,
      error: error instanceof Error ? error.message : 'Error desconocido al eliminar.',
    }
  }
}

/**
 * Verifica si hay espacio disponible en localStorage.
 */
export function hayEspacioDisponible(): boolean {
  try {
    const prueba = `${PREFIJO_APP}_prueba_espacio`
    localStorage.setItem(prueba, '1')
    localStorage.removeItem(prueba)
    return true
  } catch {
    return false
  }
}
