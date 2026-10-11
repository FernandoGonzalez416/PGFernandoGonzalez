import { useCallback, useEffect, useState } from 'react'
import { limpiarCacheApi } from '../api/client'
import type { SugerenciaRead } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarSugerencias } from '../services/sugerencias'

export type EstadoSugerencia = 'pendiente' | 'atendida' | 'descartada'
export type FiltroEstado = EstadoSugerencia | 'todas'

export function useSugerencias(tamanoPagina = 20) {
  const [filtro, setFiltro] = useState<FiltroEstado>('pendiente')
  const [sugerencias, setSugerencias] = useState<SugerenciaRead[]>([])
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(0)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refresco, setRefresco] = useState(0)

  const recargar = useCallback(() => { limpiarCacheApi(); setRefresco((valor) => valor + 1) }, [])

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    setPagina((p) => (p !== 0 ? 0 : p))
  }, [filtro])
/* eslint-enable react-hooks/set-state-in-effect */

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      setCargando(true)
      try {
        const datos = await listarSugerencias({
          estado: filtro === 'todas' ? undefined : filtro,
          limite: tamanoPagina,
          desplazamiento: pagina * tamanoPagina,
        })
        if (activo) {
          setSugerencias(datos.items)
          setTotal(datos.total)
          setError(null)
        }
      } catch (fallo) {
        if (activo) setError(mensajeDeError(fallo))
      } finally {
        if (activo) setCargando(false)
      }
    }
    void cargar()
    return () => {
      activo = false
    }
  }, [filtro, pagina, tamanoPagina, refresco])

  const hayMas = (pagina + 1) * tamanoPagina < total

  return {
    sugerencias,
    total,
    cargando,
    error,
    filtro,
    setFiltro,
    pagina,
    hayMas,
    irAnterior: () => setPagina((valor) => Math.max(0, valor - 1)),
    irSiguiente: () => setPagina((valor) => valor + 1),
    recargar,
  }
}