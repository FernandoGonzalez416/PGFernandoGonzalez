import type { components } from './schema'

export type MeRead = components['schemas']['MeRead']
export type ResumenVentas = components['schemas']['ResumenVentas']
export type ResumenVentaDia = components['schemas']['ResumenVentaDia']
export type AlertaResumen = components['schemas']['AlertaResumen']
export type AlertaStockBajo = components['schemas']['AlertaStockBajo']
export type AlertaVencimientoProximo = components['schemas']['AlertaVencimientoProximo']
export type ProductoMasVendidoItem = components['schemas']['ProductoMasVendidoItem']
export type SugerenciaRead = components['schemas']['SugerenciaRead']
export type SugerenciaUpdate = components['schemas']['SugerenciaUpdate']
export type GenerarResultado = components['schemas']['GenerarResultado']
export type ProductoRead = components['schemas']['ProductoRead']
export type ProductoCreate = components['schemas']['ProductoCreate']
export type ProductoUpdate = components['schemas']['ProductoUpdate']
export type CategoriaRead = components['schemas']['CategoriaRead']
export type CategoriaCreate = components['schemas']['CategoriaCreate']
export type CategoriaUpdate = components['schemas']['CategoriaUpdate']
export type ProveedorRead = components['schemas']['ProveedorRead']
export type ProveedorCreate = components['schemas']['ProveedorCreate']
export type ProveedorUpdate = components['schemas']['ProveedorUpdate']
export type ExistenciaRead = components['schemas']['ExistenciaRead']
export type ExistenciaAjuste = components['schemas']['ExistenciaAjuste']
export type MovimientoRead = components['schemas']['MovimientoRead']
export type VentaRead = components['schemas']['VentaRead']
export type VentaCreate = components['schemas']['VentaCreate']
export type VentaDetalleRead = components['schemas']['VentaDetalleRead']
export type VentaLineaCreate = components['schemas']['VentaDetalleCreate']
export type AnulacionCreate = components['schemas']['AnulacionCreate']

// Predicción
export type PrediccionRead = components['schemas']['PrediccionRead'] & {
  motivo?: string | null
}
export type SerieResponse = components['schemas']['SerieResponse']

export type Capacidad = MeRead['capacidades'][number]
export type Rol = MeRead['rol']

export type NotificacionItem = {
  id: string
  tipo: string
  mensaje: string
  usuario_id: string | null
  leida: boolean
  fecha: string
}

export type ListaConTotal<T> = { items: T[]; total: number }
