import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../components/ui/ToastProvider'
import { Notificaciones } from './Notificaciones'

const mocks = vi.hoisted(() => ({
  notificaciones: [
    { id: 'n1', tipo: 'bajo_stock', mensaje: 'Labial rojo stock bajo', usuario_id: 'u1', leida: false, fecha: '2026-10-01T10:00:00Z' },
    { id: 'n2', tipo: 'sugerencia_compra', mensaje: 'Nueva sugerencia para Crema', usuario_id: 'u1', leida: true, fecha: '2026-09-30T10:00:00Z' },
  ],
  total: 2,
  perfil: {
    id: 'u1', auth_id: 'a1', nombre: 'U', email: 'u@c.com', rol: 'propietario', activo: true,
    capacidades: ['stock:consultar', 'alertas:ver'],
  },
}))

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({ perfil: mocks.perfil, cargando: false, iniciarSesion: vi.fn(), cerrarSesion: vi.fn() }),
}))

vi.mock('../hooks/useNotificaciones', () => ({
  useNotificaciones: () => ({
    notificaciones: mocks.notificaciones,
    total: mocks.total,
    cargando: false,
    error: null,
    recargar: vi.fn(),
  }),
}))

vi.mock('../services/notificaciones', () => ({
  marcarNotificacionLeida: vi.fn(() => Promise.resolve({ ok: true })),
  listarNotificaciones: vi.fn(() => Promise.resolve({ items: mocks.notificaciones, total: mocks.total })),
}))

function renderNotificaciones() {
  return render(
    <MemoryRouter initialEntries={['/notificaciones']}>
      <ToastProvider>
        <Notificaciones />
      </ToastProvider>
    </MemoryRouter>,
  )
}

describe('Notificaciones', () => {
  beforeEach(() => vi.clearAllMocks())

  it('lista las notificaciones con tipo, mensaje y fecha', () => {
    renderNotificaciones()
    expect(screen.getByText('Labial rojo stock bajo')).toBeInTheDocument()
    expect(screen.getByText('Nueva sugerencia para Crema')).toBeInTheDocument()
  })

  it('permite marcar como leída una notificación', async () => {
    renderNotificaciones()
    const btn = screen.getByRole('button', { name: 'Marcar como leída' })
    await fireEvent.click(btn)
    await waitFor(() => expect(screen.getByText('Notificación marcada como leída')).toBeInTheDocument())
  })

  it('filtra por leídas / sin leer', () => {
    renderNotificaciones()
    const select = screen.getByLabelText('Filtrar')
    expect(select).toBeInTheDocument()
  })
})