import { useState, useCallback, useEffect, useRef } from 'react'
import { ApiError } from '../api/client'
import { registrarVenta } from '../services/ventas'
import { guardarDato, leerDato } from './almacenamiento'
import type { VentaCola } from './types'

const TIPO_DATO = 'cola_ventas' as const

const METODOS_PAGO = ['efectivo', 'tarjeta', 'transferencia', 'otro'] as const
type MetodoPago = (typeof METODOS_PAGO)[number]

function esMetodoPago(valor: string): valor is MetodoPago {
  return (METODOS_PAGO as readonly string[]).includes(valor)
}

/**
 * Cola de ventas offline (P27/F5).
 *
 * - Persiste en localStorage, separada por usuario (`almacenamiento.ts`).
 * - Orden FIFO, una venta a la vez.
 * - Reintenta con el mismo `client_request_id`, así el backend no duplica.
 * - 401: pausa y marca `authRequerida` sin perder la cola.
 * - 409/422/403: la venta pasa a `requiere_revision` y la sincronización sigue.
 * - Error de red: detiene y se reintenta cuando la conexión vuelva.
 *
 * La sincronización automática vive en `ProveedorOffline`, no aquí, para que
 * las pruebas unitarias del hook sean deterministas.
 */
export function useColaVentas(usuarioId: string | null, online: boolean) {
  // Hidratación perezosa desde localStorage. `ProveedorOffline` remonta este
  // hook al cambiar de usuario, así que la lectura inicial siempre corresponde
  // al usuario actual y no hace falta un efecto de carga.
  const [ventas, setVentas] = useState<VentaCola[]>(() =>
    usuarioId === null ? [] : (leerDato<VentaCola[]>(TIPO_DATO, usuarioId).datos ?? []),
  )
  const [sincronizando, setSincronizando] = useState(false)
  const [authRequerida, setAuthRequerida] = useState(false)
  const sincronizandoRef = useRef(false)

  // Persistir la cola. Solo escribe en localStorage: no llama a setState, por
  // lo que no provoca renders en cascada.
  useEffect(() => {
    if (usuarioId === null) return
    guardarDato(TIPO_DATO, usuarioId, ventas)
  }, [ventas, usuarioId])

  const agregarVenta = useCallback((venta: VentaCola) => {
    setVentas((actual) => [...actual, venta])
  }, [])

  const actualizarEstado = useCallback(
    (clientRequestId: string, estado: VentaCola['estado'], error?: string, folioDefinitivo?: string) => {
      setVentas((actual) =>
        actual.map((v) =>
          v.client_request_id === clientRequestId
            ? { ...v, estado, error: error ?? v.error, folio_definitivo: folioDefinitivo ?? v.folio_definitivo }
            : v,
        ),
      )
    },
    [],
  )

  const eliminarVenta = useCallback((clientRequestId: string) => {
    setVentas((actual) => actual.filter((v) => v.client_request_id !== clientRequestId))
  }, [])

  const sincronizar = useCallback(async (): Promise<void> => {
    if (sincronizandoRef.current) return
    if (!online) return
    if (ventas.length === 0) return
    const pendientes = ventas.filter((v) => v.estado === 'pendiente')
    if (pendientes.length === 0) return

    sincronizandoRef.current = true
    setSincronizando(true)

    for (const venta of pendientes) {
      try {
        const creada = await registrarVenta({
          lineas: venta.lineas.map((l) => ({ producto_id: l.producto_id, cantidad: l.cantidad })),
          descuento: venta.descuento,
          metodo_pago: esMetodoPago(venta.metodo_pago) ? venta.metodo_pago : 'otro',
          cliente_id: null,
          client_request_id: venta.client_request_id,
          fecha: venta.fecha,
        })
        actualizarEstado(venta.client_request_id, 'sincronizada', undefined, creada.folio)
      } catch (fallo) {
        if (fallo instanceof ApiError) {
          if (fallo.status === 401) {
            setAuthRequerida(true)
            break
          }
          if (fallo.status === 409 || fallo.status === 422 || fallo.status === 403) {
            actualizarEstado(venta.client_request_id, 'requiere_revision', fallo.message)
            continue
          }
        }
        // Error de red u otro: detener y reintentar más tarde.
        break
      }
    }

    sincronizandoRef.current = false
    setSincronizando(false)
  }, [ventas, online, actualizarEstado])

  const reintentar = useCallback(
    (clientRequestId: string) => {
      setAuthRequerida(false)
      actualizarEstado(clientRequestId, 'pendiente')
    },
    [actualizarEstado],
  )

  return {
    ventas,
    sincronizando,
    authRequerida,
    agregarVenta,
    actualizarEstado,
    eliminarVenta,
    sincronizar,
    reintentar,
  }
}
