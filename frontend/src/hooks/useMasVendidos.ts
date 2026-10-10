import { useCallback, useEffect, useState } from 'react'
import type { ProductoMasVendidoItem } from '../api/types'
import { mensajeDeError } from '../lib/errores'
import { listarProductosMasVendidos } from '../services/reportes'
import { haceDiasISO, hoyISO } from '../lib/fecha'

export function useMasVendidos(limite = 10, dias = 30) {
  const [fechaInicio, setFechaInicio] = useState(haceDiasISO(dias - 1))
  const [fechaFin, setFechaFin] = useState(hoyISO())
  const [items, setItems] = useState<ProductoMasVendidoItem[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refresco, setRefresco] = useState(0)

  const recargar = useCallback(() => setRefresco((valor) => valor + 1), [])

  useEffect(() => {
    let activo = true
    const cargar = async () => {
      setCargando(true)
      try {
        const datos = await listarProductosMasVendidos({ fechaInicio, fechaFin, limite })
        if (activo) {
          setItems(datos)
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
  }, [fechaInicio, fechaFin, limite, refresco])

  return {
    items,
    cargando,
    error,
    fechaInicio,
    fechaFin,
    setFechaInicio,
    setFechaFin,
    recargar,
  }
}