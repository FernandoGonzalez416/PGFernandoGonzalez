import { useCallback, useEffect, useState } from 'react'
import type { ResumenVentas } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { obtenerResumenVentas } from '../services/ventas'

export function useResumenVentas() {
  const [resumen, setResumen] = useState<ResumenVentas | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refresco, setRefresco] = useState(0)

  const recargar = useCallback(() => setRefresco((valor) => valor + 1), [])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      setCargando(true)
      try {
        const datos = await obtenerResumenVentas()
        if (activo) {
          setResumen(datos)
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
  }, [refresco])

  return { resumen, cargando, error, recargar }
}