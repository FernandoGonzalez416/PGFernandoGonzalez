import { apiFetch } from '../api/client'
import type {
  GenerarResultado,
  ListaConTotal,
  SugerenciaRead,
  SugerenciaUpdate,
} from '../api/types'
import { construirConsulta } from './consulta'

export type FiltrosSugerencias = {
  estado?: 'pendiente' | 'atendida' | 'descartada'
  limite?: number
  desplazamiento?: number
}

export function listarSugerencias(
  filtros: FiltrosSugerencias = {},
): Promise<ListaConTotal<SugerenciaRead>> {
  const consulta = construirConsulta({
    estado: filtros.estado,
    limite: filtros.limite,
    desplazamiento: filtros.desplazamiento,
  })
  return apiFetch<ListaConTotal<SugerenciaRead>>(`/api/sugerencias${consulta}`)
}

export function generarSugerencias(): Promise<GenerarResultado> {
  return apiFetch<GenerarResultado>('/api/sugerencias/generar', { method: 'POST' })
}

export function actualizarSugerencia(
  sugerenciaId: string,
  datos: SugerenciaUpdate,
): Promise<SugerenciaRead> {
  return apiFetch<SugerenciaRead>(`/api/sugerencias/${sugerenciaId}`, {
    method: 'PATCH',
    body: JSON.stringify(datos),
  })
}