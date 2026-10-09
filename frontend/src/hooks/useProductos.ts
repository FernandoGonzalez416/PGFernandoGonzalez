import { useCallback, useEffect, useState } from 'react'
import type { ProductoRead } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarProductos } from '../services/catalogo'

type ConsultaProductos = {
  q: string
  categoriaId: string | null
  incluirInactivos: boolean
}

function parametrosDe(consulta: ConsultaProductos) {
  return {
    q: consulta.q === '' ? undefined : consulta.q,
    categoriaId: consulta.categoriaId,
    incluirInactivos: consulta.incluirInactivos,
  }
}

export function useProductos() {
  const [productos, setProductos] = useState<ProductoRead[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [busqueda, setBusqueda] = useState('')
  const [categoriaId, setCategoriaId] = useState<string | null>(null)
  const [incluirInactivos, setIncluirInactivos] = useState(false)
  const [consulta, setConsulta] = useState<ConsultaProductos>({
    q: '',
    categoriaId: null,
    incluirInactivos: false,
  })

  useEffect(() => {
    const temporizador = window.setTimeout(() => {
      setConsulta({ q: busqueda, categoriaId, incluirInactivos })
    }, 300)
    return () => window.clearTimeout(temporizador)
  }, [busqueda, categoriaId, incluirInactivos])

  const recargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      setProductos(await listarProductos(parametrosDe(consulta)))
    } catch (fallo) {
      setError(mensajeDeError(fallo))
    } finally {
      setCargando(false)
    }
  }, [consulta])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      try {
        const datos = await listarProductos(parametrosDe(consulta))
        if (activo) {
          setProductos(datos)
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
  }, [consulta])

  return {
    productos,
    cargando,
    error,
    busqueda,
    setBusqueda,
    categoriaId,
    setCategoriaId,
    incluirInactivos,
    setIncluirInactivos,
    recargar,
  }
}
