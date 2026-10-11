import { useCallback, useEffect, useState } from 'react'
import { limpiarCacheApi } from '../api/client'
import type { ProveedorRead } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarProveedores } from '../services/catalogo'

export function useProveedores(incluirInactivos = false) {
  const [proveedores, setProveedores] = useState<ProveedorRead[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    limpiarCacheApi()
    setCargando(true)
    setError(null)
    try {
      setProveedores(await listarProveedores(incluirInactivos))
    } catch (fallo) {
      setError(mensajeDeError(fallo))
    } finally {
      setCargando(false)
    }
  }, [incluirInactivos])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      try {
        const datos = await listarProveedores(incluirInactivos)
        if (activo) {
          setProveedores(datos)
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
  }, [incluirInactivos])

  return { proveedores, cargando, error, recargar }
}
