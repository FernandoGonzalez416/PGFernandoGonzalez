import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../components/ui/ToastProvider'
import { Inventario } from './Inventario'

const mocks = vi.hoisted(() => ({
  ajustarExistencia: vi.fn(),
  cantidad: '5.00',
  perfil: {
    id: 'usuario-1',
    auth_id: 'auth-1',
    nombre: 'Usuario',
    email: 'usuario@correo.com',
    rol: 'propietario',
    activo: true,
    capacidades: ['inventario:ajustar', 'inventario:ver_movimientos', 'stock:consultar'],
  } as Record<string, unknown>,
}))

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({
    perfil: mocks.perfil,
    cargando: false,
    iniciarSesion: vi.fn(),
    cerrarSesion: vi.fn(),
  }),
}))

vi.mock('../hooks/useProductos', async () => {
  const { crearProducto } = await import('../test/fixtures')
  return {
    useProductos: () => ({
      productos: [
        crearProducto({
          id: 'prod-1',
          codigo: 'SIM-001',
          nombre: 'Labial mate',
          umbral_minimo: '3',
          existencia: mocks.cantidad,
        }),
      ],
      cargando: false,
      error: null,
      busqueda: '',
      setBusqueda: vi.fn(),
      categoriaId: null,
      setCategoriaId: vi.fn(),
      incluirInactivos: false,
      setIncluirInactivos: vi.fn(),
      recargar: vi.fn(),
    }),
  }
})

vi.mock('../hooks/useExistencias', () => ({
  useExistencias: () => ({
    existencias: [
      {
        producto_id: 'prod-1',
        almacen_id: 'alm-1',
        almacen_nombre: 'Principal',
        cantidad: mocks.cantidad,
        updated_at: '2026-10-01T10:00:00Z',
      },
    ],
    cargando: false,
    error: null,
    recargar: vi.fn(),
  }),
}))

vi.mock('../hooks/useMovimientos', () => ({
  useMovimientos: () => ({ movimientos: [], cargando: false, error: null, recargar: vi.fn() }),
}))

vi.mock('../services/inventario', () => ({ ajustarExistencia: mocks.ajustarExistencia }))

function montar() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <Inventario />
      </ToastProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  mocks.ajustarExistencia.mockReset()
  mocks.cantidad = '5.00'
  mocks.perfil.capacidades = ['inventario:ajustar', 'inventario:ver_movimientos', 'stock:consultar']
})

describe('Inventario · existencias', () => {
  it('muestra el estado Bajo cuando la existencia no supera el umbral', () => {
    mocks.cantidad = '2.00'
    montar()
    expect(screen.getByText('Bajo')).toBeInTheDocument()
  })

  it('muestra el estado Disponible cuando hay existencia suficiente', () => {
    montar()
    expect(screen.getByText('Disponible')).toBeInTheDocument()
  })
})

describe('Inventario · ajustes', () => {
  it('envía la cantidad firmada y la nota al ajustar', async () => {
    mocks.ajustarExistencia.mockResolvedValue({
      producto_id: 'prod-1',
      almacen_id: 'alm-1',
      almacen_nombre: 'Principal',
      cantidad: '2.00',
      updated_at: '2026-10-01T10:00:00Z',
    })
    montar()
    fireEvent.click(screen.getByRole('button', { name: 'Ajustar' }))

    const dialogo = await screen.findByRole('dialog', { name: 'Ajustar existencia' })
    fireEvent.change(within(dialogo).getByLabelText('Cantidad a ajustar'), {
      target: { value: '-3' },
    })
    fireEvent.change(within(dialogo).getByLabelText('Nota'), { target: { value: 'Merma' } })
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Aplicar ajuste' }))

    await waitFor(() =>
      expect(mocks.ajustarExistencia).toHaveBeenCalledWith({
        producto_id: 'prod-1',
        cantidad: -3,
        nota: 'Merma',
      }),
    )
  })

  it('rechaza un ajuste con cantidad cero', async () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: 'Ajustar' }))
    const dialogo = await screen.findByRole('dialog', { name: 'Ajustar existencia' })
    fireEvent.change(within(dialogo).getByLabelText('Cantidad a ajustar'), {
      target: { value: '0' },
    })
    fireEvent.change(within(dialogo).getByLabelText('Nota'), { target: { value: 'Prueba' } })
    fireEvent.click(within(dialogo).getByRole('button', { name: 'Aplicar ajuste' }))

    expect(
      await screen.findByText('Escribe una cantidad distinta de cero (positivo suma, negativo resta).'),
    ).toBeInTheDocument()
    expect(mocks.ajustarExistencia).not.toHaveBeenCalled()
  })
})
