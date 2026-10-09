import { useCallback, useEffect, useState } from 'react'
import type { ExistenciaRead } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarExistencias } from '../services/inventario'

export function useExistencias() {
  const [existencias, setExistencias] = useState<ExistenciaRead[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refresco, setRefresco] = useState(0)

  const recargar = useCallback(() => setRefresco((valor) => valor + 1), [])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      setCargando(true)
      try {
        const datos = await listarExistencias()
        if (activo) {
          setExistencias(datos)
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

  return { existencias, cargando, error, recargar }
}
