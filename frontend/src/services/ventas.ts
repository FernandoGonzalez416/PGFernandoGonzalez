import { apiFetch } from '../api/client'
import type { AnulacionCreate, VentaCreate, VentaRead } from '../api/types'
import { construirConsulta } from './consulta'

export type FiltrosVentas = {
  limite?: number
  desplazamiento?: number
}

export function listarVentas(filtros: FiltrosVentas = {}): Promise<VentaRead[]> {
  const consulta = construirConsulta({
    limite: filtros.limite,
    desplazamiento: filtros.desplazamiento,
  })
  return apiFetch<VentaRead[]>(`/api/ventas${consulta}`)
}

export function obtenerVenta(ventaId: string): Promise<VentaRead> {
  return apiFetch<VentaRead>(`/api/ventas/${ventaId}`)
}

export function registrarVenta(datos: VentaCreate): Promise<VentaRead> {
  return apiFetch<VentaRead>('/api/ventas', {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

export function anularVenta(ventaId: string, datos: AnulacionCreate): Promise<VentaRead> {
  return apiFetch<VentaRead>(`/api/ventas/${ventaId}/anular`, {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}
