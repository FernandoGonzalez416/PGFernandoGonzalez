import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { VentaRecibo } from './VentaRecibo'

function ventaBase(overrides: Record<string, unknown> = {}) {
  return {
    id: 'v1',
    folio: 'F-2026-0007',
    fecha: '2026-10-01T10:00:00Z',
    cliente_id: null,
    usuario_id: 'usuario-1',
    metodo_pago: 'tarjeta',
    subtotal: '30.00',
    descuento: '5.00',
    total: '25.00',
    estado: 'registrada',
    motivo_anulacion: null,
    lineas: [
      {
        producto_id: 'prod-1',
        producto_nombre: 'Labial mate',
        cantidad: 2,
        precio_unitario: '15.00',
        subtotal: '30.00',
      },
    ],
    ...overrides,
  }
}

const mocks = vi.hoisted(() => ({ venta: {} as Record<string, unknown> }))

vi.mock('../hooks/useVenta', () => ({
  useVenta: () => ({ venta: mocks.venta, cargando: false, error: null, recargar: vi.fn() }),
}))

beforeEach(() => {
  mocks.venta = ventaBase()
})

function montar() {
  return render(
    <MemoryRouter>
      <VentaRecibo />
    </MemoryRouter>,
  )
}

describe('VentaRecibo', () => {
  it('muestra el folio, las líneas y la leyenda de recibo interno', () => {
    montar()
    expect(screen.getByText('F-2026-0007')).toBeInTheDocument()
    expect(screen.getByText('Labial mate')).toBeInTheDocument()
    expect(screen.getByText(/Recibo interno/)).toBeInTheDocument()
    expect(screen.getByText(/no es factura ni documento tributario/)).toBeInTheDocument()
  })

  it('marca el recibo como ANULADA y muestra el motivo cuando corresponde', () => {
    mocks.venta = ventaBase({ estado: 'anulada', motivo_anulacion: 'Cliente desistió' })
    montar()
    expect(screen.getByText('ANULADA')).toBeInTheDocument()
    expect(screen.getByText(/Cliente desistió/)).toBeInTheDocument()
  })

  it('no muestra la marca ANULADA en una venta registrada', () => {
    montar()
    expect(screen.queryByText('ANULADA')).not.toBeInTheDocument()
  })
})
