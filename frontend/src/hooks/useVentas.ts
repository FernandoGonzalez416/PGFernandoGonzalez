import { useCallback, useEffect, useState } from 'react'
import { limpiarCacheApi } from '../api/client'
import type { VentaRead } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarVentas } from '../services/ventas'

export function useVentas(tamanoPagina = 20) {
  const [ventas, setVentas] = useState<VentaRead[]>([])
  const [pagina, setPagina] = useState(0)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hayMas, setHayMas] = useState(false)
  const [refresco, setRefresco] = useState(0)

  const desplazamiento = pagina * tamanoPagina

  const recargar = useCallback(() => { limpiarCacheApi(); setRefresco((valor) => valor + 1) }, [])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      setCargando(true)
      try {
        const datos = await listarVentas({ limite: tamanoPagina, desplazamiento })
        if (activo) {
          setVentas(datos)
          setHayMas(datos.length === tamanoPagina)
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
  }, [desplazamiento, tamanoPagina, refresco])

  return {
    ventas,
    cargando,
    error,
    pagina,
    hayMas,
    irAnterior: () => setPagina((valor) => Math.max(0, valor - 1)),
    irSiguiente: () => setPagina((valor) => valor + 1),
    recargar,
  }
}
