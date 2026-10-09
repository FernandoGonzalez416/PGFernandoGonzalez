import { useCallback, useEffect, useState } from 'react'
import type { MovimientoRead } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarMovimientos } from '../services/inventario'

export function useMovimientos(limite = 50) {
  const [movimientos, setMovimientos] = useState<MovimientoRead[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refresco, setRefresco] = useState(0)

  const recargar = useCallback(() => setRefresco((valor) => valor + 1), [])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      setCargando(true)
      try {
        const datos = await listarMovimientos({ limite })
        if (activo) {
          setMovimientos(datos)
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
  }, [limite, refresco])

  return { movimientos, cargando, error, recargar }
}
