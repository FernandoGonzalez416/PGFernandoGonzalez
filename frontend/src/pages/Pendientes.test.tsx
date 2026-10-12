import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { EstadoOffline } from '../offline/contexto'
import { useOffline } from '../offline/useOffline'
import type { VentaCola } from '../offline/types'
import { VentasPendientes } from './VentasPendientes'

vi.mock('../offline/useOffline', () => ({ useOffline: vi.fn() }))

function estado(overrides: Partial<EstadoOffline> = {}): EstadoOffline {
  return {
    usuarioId: 'user1',
    online: true,
    sincronizando: false,
    authRequerida: false,
    pendientes: 0,
    ventas: [],
    productos: [],
    catalogoCargando: false,
    fechaDescarga: null,
    agregarVenta: vi.fn(),
    actualizarEstado: vi.fn(),
    eliminarVenta: vi.fn(),
    sincronizar: vi.fn(),
    reintentar: vi.fn(),
    actualizarCache: vi.fn(),
    buscarPorCodigo: vi.fn(),
    buscarPorNombre: vi.fn(),
    descontarExistencia: vi.fn(),
    ...overrides,
  }
}

beforeEach(() => {
  vi.mocked(useOffline).mockReturnValue(estado())
})

describe('VentasPendientes', () => {
  it('muestra la tabla de ventas pendientes', () => {
    render(<VentasPendientes />)
    expect(screen.getByText('Ventas pendientes')).toBeDefined()
    expect(screen.getByText('Folio')).toBeDefined()
    expect(screen.getByText('Estado')).toBeDefined()
    expect(screen.getByText('Total')).toBeDefined()
  })

  it('muestra acción Reintentar para ventas que requieren revisión', () => {
    const ventaRevision: VentaCola = {
      client_request_id: 'req-1',
      folio_provisional: 'T-0001',
      folio_definitivo: null,
      fecha: new Date().toISOString(),
      lineas: [{ producto_id: 'p1', nombre: 'Labial', cantidad: 1, precio_unitario: 50, subtotal: 50 }],
      subtotal: 50,
      descuento: 0,
      total: 50,
      metodo_pago: 'efectivo',
      estado: 'requiere_revision',
      error: 'Stock insuficiente',
      usuario_id: 'user1',
    }
    vi.mocked(useOffline).mockReturnValue(estado({ ventas: [ventaRevision], pendientes: 1 }))

    render(<VentasPendientes />)

    expect(screen.getByText('Reintentar')).toBeDefined()
  })
})
