import { useCallback, useEffect, useState } from 'react'
import type { VentaRead } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { obtenerVenta } from '../services/ventas'

export function useVenta(ventaId: string | undefined) {
  const idValido = ventaId !== undefined && ventaId !== ''
  const [venta, setVenta] = useState<VentaRead | null>(null)
  const [cargando, setCargando] = useState(idValido)
  const [error, setError] = useState<string | null>(idValido ? null : 'No se indicó la venta.')
  const [refresco, setRefresco] = useState(0)

  const recargar = useCallback(() => setRefresco((valor) => valor + 1), [])

  useEffect(() => {
    if (ventaId === undefined || ventaId === '') return
    let activo = true
    const cargar = async () => {
      setCargando(true)
      try {
        const datos = await obtenerVenta(ventaId)
        if (activo) {
          setVenta(datos)
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
  }, [ventaId, refresco])

  return { venta, cargando, error, recargar }
}
