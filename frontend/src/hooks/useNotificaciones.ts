import { useCallback, useEffect, useState } from 'react'
import type { NotificacionItem } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarNotificaciones, type FiltrosNotificaciones } from '../services/notificaciones'

export function useNotificaciones(filtros: FiltrosNotificaciones = {}) {
  const leida = filtros.leida
  const limite = filtros.limite ?? 50

  const [notificaciones, setNotificaciones] = useState<NotificacionItem[]>([])
  const [total, setTotal] = useState(0)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refresco, setRefresco] = useState(0)

  const recargar = useCallback(() => setRefresco((valor) => valor + 1), [])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      setCargando(true)
      try {
        const datos = await listarNotificaciones({ leida, limite })
        if (activo) {
          setNotificaciones(datos.items)
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
  }, [leida, limite, refresco])

  return { notificaciones, total, cargando, error, recargar }
}