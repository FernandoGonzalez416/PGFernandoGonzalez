import { useCallback, useEffect, useState } from 'react'
import { limpiarCacheApi } from '../api/client'
import type { CategoriaRead } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarCategorias } from '../services/catalogo'

export function useCategorias(incluirInactivas = false) {
  const [categorias, setCategorias] = useState<CategoriaRead[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    limpiarCacheApi()
    setCargando(true)
    setError(null)
    try {
      setCategorias(await listarCategorias(incluirInactivas))
    } catch (fallo) {
      setError(mensajeDeError(fallo))
    } finally {
      setCargando(false)
    }
  }, [incluirInactivas])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      try {
        const datos = await listarCategorias(incluirInactivas)
        if (activo) {
          setCategorias(datos)
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
  }, [incluirInactivas])

  return { categorias, cargando, error, recargar }
}
