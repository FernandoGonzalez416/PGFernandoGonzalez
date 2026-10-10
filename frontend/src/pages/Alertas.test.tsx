import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../components/ui/ToastProvider'
import { Alertas } from './Alertas'

const mocks = {
  alertas: {
    bajo_stock: [
      { producto_id: 'p1', codigo: 'SIM-001', nombre: 'Labial rojo', existencia: 0, umbral_minimo: 5, agotado: true },
      { producto_id: 'p2', codigo: 'SIM-002', nombre: 'Crema facial', existencia: 2, umbral_minimo: 5, agotado: false },
    ],
    vencimiento_proximo: [
      { producto_id: 'p3', codigo: 'SIM-003', nombre: 'Sombra ojos', fecha_vencimiento: '2026-10-10', dias_vencimiento_aviso: 30, dias_restantes: 0, vencido: true },
      { producto_id: 'p4', codigo: 'SIM-004', nombre: 'Perfume', fecha_vencimiento: '2026-10-20', dias_vencimiento_aviso: 30, dias_restantes: 10, vencido: false },
    ],
    alertasVacia: { bajo_stock: [], vencimiento_proximo: [] },
    perfil: {
      id: 'u1', auth_id: 'a1', nombre: 'U', email: 'u@c.com', rol: 'propietario', activo: true,
      capacidades: ['stock:consultar', 'alertas:ver'],
    },
    showEmpty: { current: false },
  },
}

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ perfil: mocks.perfil, cargando: false, iniciarSesion: vi.fn(), cerrarSesion: vi.fn() }),
}))

vi.mock('../hooks/useAlertas', () => ({
  useAlertas: () => ({
    alertas: mocks.showEmpty.current ? mocks.alertasVacia : mocks.alertas,
    cargando: false,
    error: null,
    recargar: vi.fn(),
  }),
}))

function renderAlertas() {
  return render(
    <MemoryRouter initialEntries={['/alertas']}>
      <ToastProvider>
        <Alertas />
      </ToastProvider>
    </MemoryRouter>,
  )
}

describe('Alertas', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.showEmpty.current = false
  })

  it('muestra pill Agotado para existencia 0', () => {
    renderAlertas()
    expect(screen.getByText('Agotado')).toBeInTheDocument()
  })

  it('muestra pill Vencido para dias_restantes <= 0', () => {
    renderAlertas()
    expect(screen.getByText('Vencido')).toBeInTheDocument()
  })

  it('muestra pill Por vencer con dias restantes', () => {
    renderAlertas()
    expect(screen.getByText('Faltan 10 dias')).toBeInTheDocument()
  })

  it('muestra estado vacio cuando no hay alertas', () => {
    mocks.showEmpty.current = true
    renderAlertas()
    expect(screen.getByText('Sin alertas en este momento.')).toBeInTheDocument()
  })
})