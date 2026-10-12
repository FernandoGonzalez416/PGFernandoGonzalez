import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import { ToastProvider } from '../components/ui/ToastProvider'
import { ProveedorOffline } from '../offline/ProveedorOffline'
import { VentaNueva } from './VentaNueva'

const mocks = vi.hoisted(() => ({ registrarVenta: vi.fn() }))

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ perfil: { id: 'user-1' }, cargando: false, iniciarSesion: vi.fn(), cerrarSesion: vi.fn() }),
}))

vi.mock('../services/catalogo', () => ({ listarProductos: vi.fn().mockResolvedValue([]) }))

vi.mock('../hooks/useProductos', async () => {
  const { useState } = await import('react')
  const productos = [
    {
      id: 'prod-1',
      codigo: 'SIM-001',
      nombre: 'Labial mate',
      precio_venta: '25.00',
      existencia: '10.00',
      unidad_medida: 'unidad',
    },
    {
      id: 'prod-2',
      codigo: 'SIM-002',
      nombre: 'Crema facial',
      precio_venta: '10.00',
      existencia: '1.00',
      unidad_medida: 'unidad',
    },
  ]
  return {
    useProductos: () => {
      const [busqueda, setBusqueda] = useState('')
      return {
        productos,
        cargando: false,
        error: null,
        busqueda,
        setBusqueda,
        categoriaId: null,
        setCategoriaId: vi.fn(),
        incluirInactivos: false,
        setIncluirInactivos: vi.fn(),
        recargar: vi.fn(),
      }
    },
  }
})

vi.mock('../services/ventas', () => ({ registrarVenta: mocks.registrarVenta }))

function montar() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <ProveedorOffline>
          <VentaNueva />
        </ProveedorOffline>
      </ToastProvider>
    </MemoryRouter>,
  )
}

function escanear(codigo: string) {
  const campo = screen.getByLabelText('Buscar producto')
  fireEvent.change(campo, { target: { value: codigo } })
  fireEvent.keyDown(campo, { key: 'Enter' })
}

beforeEach(() => {
  mocks.registrarVenta.mockReset()
})

describe('VentaNueva', () => {
  it('deshabilita Cobrar mientras el carrito está vacío', () => {
    montar()
    expect(screen.getByRole('button', { name: /Cobrar/ })).toBeDisabled()
  })

  it('agrega el producto al carrito al escanear su código y pulsar Enter', () => {
    montar()
    escanear('SIM-001')
    const cobrar = screen.getByRole('button', { name: /Cobrar/ })
    expect(cobrar).toBeEnabled()
    expect(cobrar).toHaveTextContent('Q 25.00')
  })

  it('envía solo las líneas con producto_id y cantidad, dejando el total al backend', async () => {
    mocks.registrarVenta.mockResolvedValue({ id: 'v1', folio: 'F-2026-0001' })
    montar()
    escanear('SIM-001')
    fireEvent.click(screen.getByRole('button', { name: /Cobrar/ }))

    await waitFor(() => expect(mocks.registrarVenta).toHaveBeenCalledTimes(1))
    expect(mocks.registrarVenta).toHaveBeenCalledWith({
      lineas: [{ producto_id: 'prod-1', cantidad: 1 }],
      descuento: '0.00',
      metodo_pago: 'efectivo',
      cliente_id: null,
    })
  })

  it('no registra la venta dos veces si se pulsa Cobrar repetidamente', async () => {
    let resolver: (valor: unknown) => void = () => {}
    mocks.registrarVenta.mockImplementation(
      () =>
        new Promise((res) => {
          resolver = res
        }),
    )
    montar()
    escanear('SIM-001')
    const cobrar = screen.getByRole('button', { name: /Cobrar/ })
    fireEvent.click(cobrar)
    fireEvent.click(cobrar)

    expect(mocks.registrarVenta).toHaveBeenCalledTimes(1)
    resolver({ id: 'v1' })
    await waitFor(() => expect(cobrar).toBeEnabled())
  })

  it('conserva el carrito y muestra el conflicto cuando el backend responde 409', async () => {
    mocks.registrarVenta.mockRejectedValue(new ApiError(409, 'Stock insuficiente para la venta.'))
    montar()
    escanear('SIM-001')
    fireEvent.click(screen.getByRole('button', { name: /Cobrar/ }))

    expect(await screen.findByText('Stock insuficiente para la venta.')).toBeInTheDocument()
    const cobrar = screen.getByRole('button', { name: /Cobrar/ })
    expect(cobrar).toBeEnabled()
    expect(cobrar).toHaveTextContent('Q 25.00')
  })

  it('quita la línea del carrito con el botón Quitar', () => {
    montar()
    escanear('SIM-001')
    expect(screen.getByRole('button', { name: /Cobrar/ })).toBeEnabled()
    fireEvent.click(screen.getByRole('button', { name: 'Quitar' }))
    expect(screen.getByRole('button', { name: /Cobrar/ })).toBeDisabled()
    expect(screen.getByText('Aún no hay productos')).toBeInTheDocument()
  })

  it('quita la línea al restar cuando la cantidad es 1', () => {
    montar()
    escanear('SIM-001')
    fireEvent.click(
      screen.getByRole('button', { name: 'Quitar Labial mate del carrito' }),
    )
    expect(screen.getByRole('button', { name: /Cobrar/ })).toBeDisabled()
  })

  it('vacía el carrito con el botón Vaciar', () => {
    montar()
    escanear('SIM-001')
    escanear('SIM-002')
    fireEvent.click(screen.getByRole('button', { name: 'Vaciar carrito' }))
    expect(screen.getByRole('button', { name: /Cobrar/ })).toBeDisabled()
    expect(screen.getByText('Aún no hay productos')).toBeInTheDocument()
  })
})
