import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../components/ui/ToastProvider'
import { VentaDetalle } from './VentaDetalle'

function ventaBase(overrides: Record<string, unknown> = {}) {
  return {
    id: 'v1',
    folio: 'F-2026-0001',
    fecha: '2026-10-01T10:00:00Z',
    cliente_id: null,
    usuario_id: 'usuario-1',
    metodo_pago: 'efectivo',
    subtotal: '25.00',
    descuento: '0.00',
    total: '25.00',
    estado: 'registrada',
    motivo_anulacion: null,
    lineas: [
      {
        producto_id: 'prod-1',
        producto_nombre: 'Labial mate',
        cantidad: 1,
        precio_unitario: '25.00',
        subtotal: '25.00',
      },
    ],
    ...overrides,
  }
}

const mocks = vi.hoisted(() => ({
  anularVenta: vi.fn(),
  perfil: {
    id: 'usuario-1',
    auth_id: 'auth-1',
    nombre: 'Usuario',
    email: 'usuario@correo.com',
    rol: 'padre',
    activo: true,
    capacidades: ['ventas:anular', 'stock:consultar'],
  } as Record<string, unknown>,
  venta: {} as Record<string, unknown>,
}))

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({
    perfil: mocks.perfil,
    cargando: false,
    iniciarSesion: vi.fn(),
    cerrarSesion: vi.fn(),
  }),
}))

vi.mock('../hooks/useVenta', () => ({
  useVenta: () => ({ venta: mocks.venta, cargando: false, error: null, recargar: vi.fn() }),
}))

vi.mock('../services/ventas', () => ({ anularVenta: mocks.anularVenta }))

function montar() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <VentaDetalle />
      </ToastProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  mocks.anularVenta.mockReset()
  mocks.perfil.rol = 'padre'
  mocks.perfil.capacidades = ['ventas:anular', 'stock:consultar']
  mocks.venta = ventaBase()
})

describe('VentaDetalle · anulación', () => {
  it('permite al padre anular una venta propia', () => {
    mocks.venta = ventaBase({ usuario_id: 'usuario-1' })
    montar()
    expect(screen.getByRole('button', { name: 'Anular venta' })).toBeInTheDocument()
  })

  it('oculta la anulación al padre en ventas ajenas', () => {
    mocks.venta = ventaBase({ usuario_id: 'otro-usuario' })
    montar()
    expect(screen.queryByRole('button', { name: 'Anular venta' })).not.toBeInTheDocument()
  })

  it('permite al propietario anular ventas de otros', () => {
    mocks.perfil.rol = 'propietario'
    mocks.venta = ventaBase({ usuario_id: 'otro-usuario' })
    montar()
    expect(screen.getByRole('button', { name: 'Anular venta' })).toBeInTheDocument()
  })

  it('envía el motivo al confirmar la anulación', async () => {
    mocks.anularVenta.mockResolvedValue(ventaBase({ estado: 'anulada' }))
    montar()
    fireEvent.click(screen.getByRole('button', { name: 'Anular venta' }))

    const dialogo = await screen.findByRole('dialog', { name: 'Anular venta' })
    fireEvent.change(within(dialogo).getByLabelText('Motivo de la anulación'), {
      target: { value: 'Error de cobro' },
    })
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Anular venta' }))

    await waitFor(() =>
      expect(mocks.anularVenta).toHaveBeenCalledWith('v1', { motivo_anulacion: 'Error de cobro' }),
    )
  })

  it('exige un motivo antes de anular', async () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: 'Anular venta' }))
    const dialogo = await screen.findByRole('dialog', { name: 'Anular venta' })
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Anular venta' }))

    expect(await screen.findByText('Escribe el motivo de la anulación.')).toBeInTheDocument()
    expect(mocks.anularVenta).not.toHaveBeenCalled()
  })
})
