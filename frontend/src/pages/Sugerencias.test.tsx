import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../components/ui/ToastProvider'
import { Sugerencias } from './Sugerencias'

const mocks = vi.hoisted(() => ({
  sugerencias: [
    { id: 's1', producto_id: 'p1', nombre: 'Labial rojo', codigo: 'SIM-001', cantidad_sugerida: '10', prioridad: 'alta', estado: 'pendiente', stock_proyectado: '5', demanda_pronosticada: '15', fecha: '2026-10-01T00:00:00Z', metodo: 'random_forest', nivel_confianza: 'alta' },
    { id: 's2', producto_id: 'p2', nombre: 'Crema facial', codigo: 'SIM-002', cantidad_sugerida: '5', prioridad: 'media', estado: 'atendida', stock_proyectado: '10', demanda_pronosticada: '10', fecha: '2026-09-25T00:00:00Z', metodo: 'promedio_movil', nivel_confianza: 'baja' },
  ],
  generar: { sugerencias_creadas: 3, predicciones_creadas: 2, por_metodo: { random_forest: 1, promedio_movil: 1 } },
  actualizar: { id: 's1', estado: 'atendida' },
  error409: { response: { status: 409, data: { detail: 'Sugerencia no está pendiente' } } },
  perfil: {
    id: 'u1', auth_id: 'a1', nombre: 'U', email: 'u@c.com', rol: 'propietario', activo: true,
    capacidades: ['stock:consultar', 'sugerencias:ver', 'sugerencias:atender', 'prediccion:ver'],
  },
  canMap: { current: new Map<string, boolean>() },
  actualizarError: { current: false },
}))

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ perfil: mocks.perfil, cargando: false, iniciarSesion: vi.fn(), cerrarSesion: vi.fn() }),
}))

vi.mock('../hooks/useSugerencias', () => ({
  useSugerencias: () => ({
    sugerencias: mocks.sugerencias,
    total: 2,
    cargando: false,
    error: null,
    recargar: vi.fn(),
    filtro: 'pendiente',
    setFiltro: vi.fn(),
    pagina: 0,
    hayMas: false,
    irAnterior: vi.fn(),
    irSiguiente: vi.fn(),
  }),
}))

vi.mock('../services/sugerencias', () => ({
  generarSugerencias: vi.fn(() => Promise.resolve(mocks.generar)),
  actualizarSugerencia: vi.fn((_id, data) => {
    if (mocks.actualizarError.current) return Promise.reject(mocks.error409)
    if (data.estado === 'atendida') return Promise.resolve(mocks.actualizar)
    return Promise.resolve({ ...mocks.actualizar, estado: 'descartada' })
  }),
}))

vi.mock('../auth/useCan', () => ({
  useCan: (cap: string) => mocks.canMap.current.get(cap) ?? false,
}))

function renderSugerencias() {
  mocks.canMap.current.set('sugerencias:ver', true)
  mocks.canMap.current.set('sugerencias:atender', true)
  mocks.canMap.current.set('prediccion:ver', true)
  return render(
    <MemoryRouter initialEntries={['/sugerencias']}>
      <ToastProvider>
        <Sugerencias />
      </ToastProvider>
    </MemoryRouter>,
  )
}

describe('Sugerencias', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.canMap.current.clear()
    mocks.canMap.current.set('sugerencias:ver', true)
    mocks.canMap.current.set('sugerencias:atender', true)
    mocks.canMap.current.set('prediccion:ver', true)
    mocks.actualizarError.current = false
  })

  it('muestra el mensaje de modelo seleccionado por validación temporal', () => {
    renderSugerencias()
    expect(screen.getByText(/modelo seleccionado por validación temporal/i)).toBeInTheDocument()
  })

  it('muestra columnas Método y Confianza en la tabla', () => {
    renderSugerencias()
    expect(screen.getByText('Método')).toBeInTheDocument()
    expect(screen.getByText('Confianza')).toBeInTheDocument()
    expect(screen.getByText('Random Forest')).toBeInTheDocument()
    expect(screen.getByText('Promedio móvil')).toBeInTheDocument()
    expect(screen.getByText('Alta')).toBeInTheDocument()
    expect(screen.getByText('Baja')).toBeInTheDocument()
  })

  it('permite atender una sugerencia pendiente', async () => {
    renderSugerencias()
    const btnAtender = screen.getByRole('button', { name: 'Atender' })
    await fireEvent.click(btnAtender)
    await waitFor(() => expect(screen.getByText('Sugerencia atendida')).toBeInTheDocument())
  })

  it('permite descartar una sugerencia pendiente', async () => {
    renderSugerencias()
    const btnDescartar = screen.getByRole('button', { name: 'Descartar' })
    await fireEvent.click(btnDescartar)
    await waitFor(() => expect(screen.getByText('Sugerencia descartada')).toBeInTheDocument())
  })

  it('muestra error 409 al atender sugerencia no pendiente', async () => {
    mocks.actualizarError.current = true
    renderSugerencias()
    const btnAtender = screen.getByRole('button', { name: 'Atender' })
    await fireEvent.click(btnAtender)
    await waitFor(() => expect(screen.getByText('Sugerencia no está pendiente')).toBeInTheDocument())
  })

  it('generar sugerencias solo visible si tiene prediccion:ver', () => {
    mocks.canMap.current.set('prediccion:ver', false)
    renderSugerencias()
    expect(screen.queryByRole('button', { name: /generar sugerencias/i })).not.toBeInTheDocument()
  })
})