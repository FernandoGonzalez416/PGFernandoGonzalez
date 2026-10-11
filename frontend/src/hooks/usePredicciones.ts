import { useCallback, useEffect, useRef, useState } from 'react'
import type { PrediccionRead, SerieResponse } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarPredicciones, obtenerSeriePrediccion } from '../services/predicciones'

export function usePredicciones() {
  const [predicciones, setPredicciones] = useState<PrediccionRead[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refresco, setRefresco] = useState(0)

  const recargar = useCallback(() => setRefresco((v) => v + 1), [])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      setCargando(true)
      try {
        const datos = await listarPredicciones()
        if (activo) {
          setPredicciones(datos)
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

  return { predicciones, cargando, error, recargar }
}

export function useSeriePrediccion(productoId: string | null) {
  const [serie, setSerie] = useState<SerieResponse | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isMounted = useRef(true)

  useEffect(() => {
    if (!productoId) {
      return
    }
    isMounted.current = true
    // Use a callback to avoid synchronous setState in effect body
    const cargar = async () => {
      setCargando(true)
      setError(null)
      try {
        const datos = await obtenerSeriePrediccion(productoId)
        if (isMounted.current) {
          setSerie(datos)
        }
      } catch (fallo) {
        if (isMounted.current) setError(mensajeDeError(fallo))
      } finally {
        if (isMounted.current) setCargando(false)
      }
    }
    void cargar()
    return () => {
      isMounted.current = false
    }
  }, [productoId])

  return { serie, cargando, error }
}