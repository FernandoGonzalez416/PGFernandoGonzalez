import { useState, useCallback } from 'react'
import { guardarDato, leerDato } from './almacenamiento'
import type { ProductoCache } from './types'

const TIPO_DATO = 'catalogo_cache' as const

function cacheInicial(usuarioId: string | null): ProductoCache[] {
  if (usuarioId === null) return []
  return leerDato<ProductoCache[]>(TIPO_DATO, usuarioId).datos ?? []
}

/**
 * Caché del catálogo de productos (P27/F5).
 *
 * - Se hidrata desde localStorage al montar (el proveedor lo remonta al cambiar
 *   de usuario, por eso no hay efecto de carga).
 * - Permite buscar por código o nombre sin conexión.
 * - Descuenta y persiste existencia local al vender offline.
 */
export function useCatalogoCache(usuarioId: string | null) {
  const [productos, setProductos] = useState<ProductoCache[]>(() => cacheInicial(usuarioId))
  const [fechaDescarga, setFechaDescarga] = useState<string | null>(
    () => cacheInicial(usuarioId)[0]?.fecha_descarga ?? null,
  )

  const actualizarCache = useCallback(
    (nuevosProductos: ProductoCache[]) => {
      setProductos(nuevosProductos)
      setFechaDescarga(nuevosProductos[0]?.fecha_descarga ?? new Date().toISOString())
      if (usuarioId !== null) guardarDato(TIPO_DATO, usuarioId, nuevosProductos)
    },
    [usuarioId],
  )

  const buscarPorCodigo = useCallback(
    (codigo: string): ProductoCache | null => {
      const codigoLower = codigo.toLowerCase()
      return productos.find((p) => p.codigo.toLowerCase() === codigoLower) ?? null
    },
    [productos],
  )

  const buscarPorNombre = useCallback(
    (nombre: string): ProductoCache[] => {
      const nombreLower = nombre.toLowerCase()
      return productos.filter((p) => p.nombre.toLowerCase().includes(nombreLower))
    },
    [productos],
  )

  const descontarExistencia = useCallback(
    (productoId: string, cantidad: number): boolean => {
      const producto = productos.find((p) => p.id === productoId)
      if (producto === undefined || producto.existencia < cantidad) return false
      const actualizados = productos.map((p) =>
        p.id === productoId ? { ...p, existencia: p.existencia - cantidad } : p,
      )
      setProductos(actualizados)
      if (usuarioId !== null) guardarDato(TIPO_DATO, usuarioId, actualizados)
      return true
    },
    [productos, usuarioId],
  )

  return {
    productos,
    fechaDescarga,
    cargando: false,
    actualizarCache,
    buscarPorCodigo,
    buscarPorNombre,
    descontarExistencia,
  }
}
