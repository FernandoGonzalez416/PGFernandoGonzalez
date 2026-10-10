import { apiFetch } from '../api/client'
import type { ProductoMasVendidoItem } from '../api/types'
import { construirConsulta } from './consulta'

export type FiltrosReporte = {
  fechaInicio?: string
  fechaFin?: string
  limite?: number
}

export function listarProductosMasVendidos(
  filtros: FiltrosReporte = {},
): Promise<ProductoMasVendidoItem[]> {
  const consulta = construirConsulta({
    fecha_inicio: filtros.fechaInicio,
    fecha_fin: filtros.fechaFin,
    limite: filtros.limite,
  })
  return apiFetch<ProductoMasVendidoItem[]>(`/api/reportes/productos-mas-vendidos${consulta}`)
}