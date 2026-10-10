import { useCallback, useEffect, useState } from 'react'
import type { AlertaResumen } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarAlertas } from '../services/alertas'

export function useAlertas() {
  const [alertas, setAlertas] = useState<AlertaResumen | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refresco, setRefresco] = useState(0)

  const recargar = useCallback(() => setRefresco((valor) => valor + 1), [])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      setCargando(true)
      try {
        const datos = await listarAlertas()
        if (activo) {
          setAlertas(datos)
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

  return { alertas, cargando, error, recargar }
}