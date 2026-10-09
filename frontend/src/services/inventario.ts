import { apiFetch } from '../api/client'
import type { ExistenciaAjuste, ExistenciaRead, MovimientoRead } from '../api/types'
import { construirConsulta } from './consulta'

export type FiltrosMovimientos = {
  productoId?: string | null
  limite?: number
  desplazamiento?: number
}

export function listarExistencias(productoId?: string | null): Promise<ExistenciaRead[]> {
  const consulta = construirConsulta({ producto_id: productoId })
  return apiFetch<ExistenciaRead[]>(`/api/inventario/existencia${consulta}`)
}

export function listarMovimientos(filtros: FiltrosMovimientos = {}): Promise<MovimientoRead[]> {
  const consulta = construirConsulta({
    producto_id: filtros.productoId,
    limite: filtros.limite,
    desplazamiento: filtros.desplazamiento,
  })
  return apiFetch<MovimientoRead[]>(`/api/inventario/movimientos${consulta}`)
}

export function ajustarExistencia(datos: ExistenciaAjuste): Promise<ExistenciaRead> {
  return apiFetch<ExistenciaRead>('/api/inventario/ajustes', {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}
