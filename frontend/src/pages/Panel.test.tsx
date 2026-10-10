import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../components/ui/ToastProvider'
import { Panel } from './Panel'

const mocks = vi.hoisted(() => ({
  resumen: {
    fecha_inicio: '2026-10-01',
    fecha_fin: '2026-10-07',
    num_ventas: 10,
    total_vendido: '1500.00',
    por_dia: [
      { fecha: '2026-10-01', num_ventas: 2, total_vendido: '300.00' },
      { fecha: '2026-10-02', num_ventas: 1, total_vendido: '150.00' },
    ],
  },
  alertas: {
    bajo_stock: [
      { producto_id: 'p1', codigo: 'SIM-001', nombre: 'Labial rojo', existencia: 2, umbral_minimo: 5, agotado: false },
    ],
    vencimiento_proximo: [
      { producto_id: 'p2', codigo: 'SIM-002', nombre: 'Crema facial', fecha_vencimiento: '2026-10-15', dias_vencimiento_aviso: 30, dias_restantes: 8, vencido: false },
    ],
  },
  masVendidos: [
    { producto_id: 'p1', codigo: 'SIM-001', nombre: 'Labial rojo', cantidad_vendida: 25, total_vendido: '500.00' },
  ],
  ultimasVentas: [
    { id: 'v1', folio: 'F-2026-0001', fecha: '2026-10-01T10:00:00Z', total: '25.00', estado: 'activa' },
  ],
  sugerencias: [
    { id: 's1', producto_id: 'p1', nombre: 'Labial rojo', codigo: 'SIM-001', cantidad_sugerida: '10', prioridad: 'alta', estado: 'pendiente', stock_proyectado: '5', demanda_pronosticada: '15', fecha: '2026-10-01T00:00:00Z' },
  ],
  perfil: {
    id: 'usuario-1', auth_id: 'auth-1', nombre: 'Usuario', email: 'u@c.com', rol: 'propietario', activo: true,
    capacidades: ['stock:consultar', 'alertas:ver', 'reportes:ver', 'sugerencias:ver'],
  },
  resumenError: { current: false },
  alertasVacia: { current: false },
}))

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ perfil: mocks.perfil, cargando: false, iniciarSesion: vi.fn(), cerrarSesion: vi.fn() }),
}))

vi.mock('../hooks/useResumenVentas', () => ({
  useResumenVentas: () => ({
    resumen: mocks.resumenError.current ? null : mocks.resumen,
    cargando: false,
    error: mocks.resumenError.current ? 'Error de red' : null,
    recargar: vi.fn(),
  }),
}))

vi.mock('../hooks/useAlertas', () => ({
  useAlertas: () => ({
    alertas: mocks.alertasVacia.current ? { bajo_stock: [], vencimiento_proximo: [] } : mocks.alertas,
    cargando: false,
    error: null,
    recargar: vi.fn(),
  }),
}))

vi.mock('../hooks/useMasVendidos', () => ({
  useMasVendidos: () => ({ items: mocks.masVendidos, cargando: false, error: null, recargar: vi.fn(), fechaInicio: '', fechaFin: '', setFechaInicio: vi.fn(), setFechaFin: vi.fn() }),
}))

vi.mock('../hooks/useVentas', () => ({
  useVentas: () => ({ ventas: mocks.ultimasVentas, cargando: false, error: null, recargar: vi.fn(), pagina: 0, hayMas: false, irAnterior: vi.fn(), irSiguiente: vi.fn() }),
}))

vi.mock('../hooks/useSugerencias', () => ({
  useSugerencias: () => ({ sugerencias: mocks.sugerencias, total: 1, cargando: false, error: null, recargar: vi.fn(), filtro: 'pendiente', setFiltro: vi.fn(), pagina: 0, hayMas: false, irAnterior: vi.fn(), irSiguiente: vi.fn() }),
}))

function renderPanel() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <ToastProvider>
        <Panel />
      </ToastProvider>
    </MemoryRouter>,
  )
}

describe('Panel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.resumenError.current = false
    mocks.alertasVacia.current = false
  })

  it('muestra los 4 bloques cuando el usuario tiene todas las capacidades', () => {
    renderPanel()
    expect(screen.getByText('Ventas de la semana')).toBeInTheDocument()
    expect(screen.getByText('Alertas')).toBeInTheDocument()
    expect(screen.getByText('Más vendidos de la semana')).toBeInTheDocument()
    expect(screen.getByText('Últimas ventas')).toBeInTheDocument()
    expect(screen.getByText('Sugerencias de compra')).toBeInTheDocument()
  })

  it('renderiza el gráfico de ventas con barras', () => {
    renderPanel()
    const svg = screen.getByRole('img', { name: /ventas por día/i })
    expect(svg).toBeInTheDocument()
  })

  it('muestra estado vacío cuando no hay alertas', () => {
    mocks.alertasVacia.current = true
    renderPanel()
    expect(screen.getByText('Sin alertas: el inventario está en orden.')).toBeInTheDocument()
  })

  it('no rompe el panel si un bloque falla (error en resumen)', () => {
    mocks.resumenError.current = true
    renderPanel()
    expect(screen.getByText('Error de red')).toBeInTheDocument()
    expect(screen.getByText('Alertas')).toBeInTheDocument()
  })
})