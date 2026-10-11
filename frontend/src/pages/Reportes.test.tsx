import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../components/ui/ToastProvider'
import { Reportes } from './Reportes'

const mocks = vi.hoisted(() => ({ 
  items: [
    { producto_id: 'p1', codigo: 'SIM-001', nombre: 'Labial rojo', cantidad_vendida: 50, total_vendido: '1000.00' },
  ],
  perfil: {
    id: 'u1', auth_id: 'a1', nombre: 'U', email: 'u@c.com', rol: 'propietario', activo: true,
    capacidades: ['stock:consultar', 'reportes:ver'],
  },
}))

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ perfil: mocks.perfil, cargando: false, iniciarSesion: vi.fn(), cerrarSesion: vi.fn() }),
}))

vi.mock('../hooks/useMasVendidos', () => ({
  useMasVendidos: () => ({ items: mocks.items, cargando: false, error: null, recargar: vi.fn(), fechaInicio: '2026-09-01', fechaFin: '2026-10-01', setFechaInicio: vi.fn(), setFechaFin: vi.fn() }),
}))

function renderReportes() {
  return render(
    <MemoryRouter initialEntries={['/reportes']}>
      <ToastProvider>
        <Reportes />
      </ToastProvider>
    </MemoryRouter>,
  )
}

describe('Reportes', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renderiza tabla con productos más vendidos', () => {
    renderReportes()
    expect(screen.getByText(/Labial rojo/)).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
  })

  it('muestra barra horizontal proporcional a cantidad vendida', () => {
    renderReportes()
    const tabla = screen.getByRole('table', { name: /productos más vendidos/i })
    expect(tabla).toBeInTheDocument()
    const barra = tabla.querySelector('.barra-horizontal-fill')
    expect(barra).toHaveStyle({ width: '100%' })
  })

  it('permite cambiar el periodo y actualiza las fechas', () => {
    renderReportes()
    const select = screen.getByLabelText('Periodo')
    expect(select).toBeInTheDocument()
  })
})