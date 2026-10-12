import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { ApiError } from '../api/client'
import { useColaVentas } from './useColaVentas'
import { useCatalogoCache } from './useCatalogoCache'
import type { VentaCola, ProductoCache } from './types'

// --- Datos ficticios de prueba ---
const venta1: VentaCola = {
  client_request_id: 'req-1',
  folio_provisional: 'T-0001',
  folio_definitivo: null,
  fecha: '2026-01-01T10:00:00Z',
  lineas: [{ producto_id: 'p1', nombre: 'Labial rojo', cantidad: 1, precio_unitario: 50, subtotal: 50 }],
  subtotal: 50,
  descuento: 0,
  total: 50,
  metodo_pago: 'efectivo',
  estado: 'pendiente',
  usuario_id: 'user-a',
}

const venta2: VentaCola = {
  client_request_id: 'req-2',
  folio_provisional: 'T-0002',
  folio_definitivo: null,
  fecha: '2026-01-01T11:00:00Z',
  lineas: [{ producto_id: 'p2', nombre: 'Base líquida', cantidad: 2, precio_unitario: 80, subtotal: 160 }],
  subtotal: 160,
  descuento: 0,
  total: 160,
  metodo_pago: 'efectivo',
  estado: 'pendiente',
  usuario_id: 'user-a',
}

const producto1: ProductoCache = {
  id: 'p1',
  codigo: 'PROD-001',
  nombre: 'Labial rojo',
  precio_venta: 50,
  existencia: 10,
  unidad_medida: 'unidad',
  fecha_descarga: '2026-01-01T10:00:00Z',
}

const producto2: ProductoCache = {
  id: 'p2',
  codigo: 'PROD-002',
  nombre: 'Base líquida',
  precio_venta: 80,
  existencia: 5,
  unidad_medida: 'unidad',
  fecha_descarga: '2026-01-01T10:00:00Z',
}

// --- Mock del servicio de ventas ---
vi.mock('../services/ventas', () => ({
  registrarVenta: vi.fn(),
}))

import { registrarVenta } from '../services/ventas'

function ventaCreada(folio: string, clientRequestId: string) {
  return {
    id: `venta-${folio}`,
    folio,
    fecha: new Date().toISOString(),
    cliente_id: null,
    usuario_id: 'user-a',
    metodo_pago: 'efectivo',
    subtotal: 50,
    descuento: 0,
    total: 50,
    estado: 'activa',
    motivo_anulacion: null,
    lineas: [],
    client_request_id: clientRequestId,
  } as never
}

describe('useColaVentas', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
    // Silenciar warnings de React sobre act en tests de hooks
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('agrega ventas en orden FIFO', () => {
    const { result } = renderHook(() => useColaVentas('user-a', true))
    act(() => {
      result.current.agregarVenta(venta1)
      result.current.agregarVenta(venta2)
    })
    expect(result.current.ventas).toHaveLength(2)
    expect(result.current.ventas[0]?.client_request_id).toBe('req-1')
    expect(result.current.ventas[1]?.client_request_id).toBe('req-2')
  })

  it('no pierde datos al recargar (persistencia)', () => {
    const { result, unmount } = renderHook(() => useColaVentas('user-a', true))
    act(() => {
      result.current.agregarVenta(venta1)
    })
    unmount()
    const { result: result2 } = renderHook(() => useColaVentas('user-a', true))
    expect(result2.current.ventas).toHaveLength(1)
    expect(result2.current.ventas[0]?.client_request_id).toBe('req-1')
  })

  it('las ventas no se mezclan entre usuarios', () => {
    const { result: resultA } = renderHook(() => useColaVentas('user-a', true))
    const { result: resultB } = renderHook(() => useColaVentas('user-b', true))
    act(() => {
      resultA.current.agregarVenta(venta1)
    })
    act(() => {
      resultB.current.agregarVenta(venta2)
    })
    expect(resultA.current.ventas).toHaveLength(1)
    expect(resultA.current.ventas[0]?.client_request_id).toBe('req-1')
    expect(resultB.current.ventas).toHaveLength(1)
    expect(resultB.current.ventas[0]?.client_request_id).toBe('req-2')
  })

  it('trata el 200 de repetición como éxito y guarda folio definitivo', async () => {
    vi.mocked(registrarVenta).mockResolvedValueOnce(ventaCreada('F-0001-0001', 'req-1'))
    const { result } = renderHook(() => useColaVentas('user-a', true))
    act(() => {
      result.current.agregarVenta(venta1)
    })
    await act(async () => {
      await result.current.sincronizar()
    })
    expect(result.current.ventas[0]?.estado).toBe('sincronizada')
    expect(result.current.ventas[0]?.folio_definitivo).toBe('F-0001-0001')
  })

  it('marca "requiere_revision" ante 409 y continúa con las demás', async () => {
    vi.mocked(registrarVenta).mockRejectedValueOnce(new ApiError(409, 'Stock insuficiente'))
    vi.mocked(registrarVenta).mockResolvedValueOnce(ventaCreada('F-0001-0002', 'req-2'))
    const { result } = renderHook(() => useColaVentas('user-a', true))
    act(() => {
      result.current.agregarVenta(venta1)
      result.current.agregarVenta(venta2)
    })
    await act(async () => {
      await result.current.sincronizar()
    })
    expect(result.current.ventas[0]?.estado).toBe('requiere_revision')
    expect(result.current.ventas[1]?.estado).toBe('sincronizada')
  })

  it('pausa la sincronización ante 401 sin perder la cola', async () => {
    vi.mocked(registrarVenta).mockRejectedValueOnce(new ApiError(401, 'No autorizado'))
    const { result } = renderHook(() => useColaVentas('user-a', true))
    act(() => {
      result.current.agregarVenta(venta1)
    })
    await act(async () => {
      await result.current.sincronizar()
    })
    expect(result.current.authRequerida).toBe(true)
    expect(result.current.ventas).toHaveLength(1)
    expect(result.current.ventas[0]?.estado).toBe('pendiente')
  })

  it('reintenta con el mismo client_request_id', async () => {
    vi.mocked(registrarVenta).mockRejectedValueOnce(new ApiError(0, 'network error'))
    vi.mocked(registrarVenta).mockResolvedValueOnce(ventaCreada('F-0001-0003', 'req-1'))
    const { result } = renderHook(() => useColaVentas('user-a', true))
    act(() => {
      result.current.agregarVenta(venta1)
    })
    await act(async () => {
      await result.current.sincronizar()
    })
    // Primer intento falló por red; el segundo debe reusar el mismo id.
    await act(async () => {
      await result.current.sincronizar()
    })
    expect(vi.mocked(registrarVenta).mock.calls[0]?.[0].client_request_id).toBe('req-1')
    expect(vi.mocked(registrarVenta).mock.calls[1]?.[0].client_request_id).toBe('req-1')
    expect(result.current.ventas[0]?.estado).toBe('sincronizada')
  })
})

describe('useCatalogoCache', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('busca productos por nombre en el caché', () => {
    const catalogo: ProductoCache[] = [{ ...producto1 }, { ...producto2 }]
    const { result } = renderHook(() => useCatalogoCache('user1'))
    act(() => {
      result.current.actualizarCache(catalogo)
    })
    // La búsqueda debe funcionar contra el caché
    expect(result.current.productos.length).toBeGreaterThan(0)
    expect(result.current.buscarPorNombre('labial')).toHaveLength(1)
  })

  it('al vender sin conexión descuenta existencia del caché', () => {
    const { result } = renderHook(() => useCatalogoCache('user1'))
    act(() => {
      result.current.actualizarCache([producto1])
    })
    const antes = result.current.productos[0]?.existencia
    act(() => {
      result.current.descontarExistencia('p1', 2)
    })
    const despues = result.current.productos[0]?.existencia
    expect(antes).toBeDefined()
    expect(despues).toBeDefined()
    expect((antes ?? 0) - (despues ?? 0)).toBe(2)
  })
})
