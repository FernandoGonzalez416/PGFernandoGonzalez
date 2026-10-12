/** Tipos del modo offline del POS (P27/F5). */

export interface ProductoCache {
  id: string
  codigo: string
  nombre: string
  precio_venta: number
  existencia: number
  unidad_medida: string
  fecha_descarga: string // ISO
}

export interface LineaVentaOffline {
  producto_id: string
  nombre: string
  cantidad: number
  precio_unitario: number
  subtotal: number
}

export type EstadoVentaCola = 'pendiente' | 'sincronizada' | 'requiere_revision'

export interface VentaCola {
  client_request_id: string
  folio_provisional: string
  folio_definitivo: string | null
  fecha: string // ISO
  lineas: LineaVentaOffline[]
  subtotal: number
  descuento: number
  total: number
  metodo_pago: string
  estado: EstadoVentaCola
  error?: string
  usuario_id: string
}

export interface EstadoSincronizacion {
  sincronizando: boolean
  ultimo_intento: string | null
  ultimo_error: string | null
}
