import { createContext } from 'react'
import type { ProductoCache, VentaCola } from './types'

/**
 * Estado offline compartido por la aplicación (P27/F5).
 *
 * Reúne el estado de conexión, la cola de ventas pendientes y el caché del
 * catálogo, para que las páginas (POS, ventas pendientes, barra superior) lean
 * exactamente la misma información en lugar de mantener copias divergentes.
 */
export type EstadoOffline = {
  usuarioId: string | null
  online: boolean
  sincronizando: boolean
  authRequerida: boolean
  pendientes: number
  ventas: VentaCola[]
  productos: ProductoCache[]
  catalogoCargando: boolean
  fechaDescarga: string | null
  agregarVenta: (venta: VentaCola) => void
  actualizarEstado: (
    clientRequestId: string,
    estado: VentaCola['estado'],
    error?: string,
    folioDefinitivo?: string,
  ) => void
  eliminarVenta: (clientRequestId: string) => void
  sincronizar: () => Promise<void>
  reintentar: (clientRequestId: string) => void
  actualizarCache: (productos: ProductoCache[]) => void
  buscarPorCodigo: (codigo: string) => ProductoCache | null
  buscarPorNombre: (nombre: string) => ProductoCache[]
  descontarExistencia: (productoId: string, cantidad: number) => boolean
}

export const ContextoOffline = createContext<EstadoOffline | null>(null)
