import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider } from '../ui/ToastProvider'
import { CampanaNotificaciones } from './CampanaNotificaciones'

const mocks = vi.hoisted(() => ({
  notificaciones: [
    { id: 'n1', tipo: 'bajo_stock', mensaje: 'Labial rojo stock bajo', usuario_id: 'u1', leida: false, fecha: '2026-10-01T10:00:00Z' },
  ],
}))

vi.mock('../../services/notificaciones', () => ({
  listarNotificaciones: vi.fn(() => Promise.resolve({
    items: mocks.notificaciones.filter((n) => !n.leida),
    total: mocks.notificaciones.filter((n) => !n.leida).length,
  })),
  marcarNotificacionLeida: vi.fn((id: string) => {
    const notificacion = mocks.notificaciones.find((n) => n.id === id)
    if (notificacion) notificacion.leida = true
    return Promise.resolve({ ok: true })
  }),
}))

function renderCampana() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <CampanaNotificaciones />
      </ToastProvider>
    </MemoryRouter>,
  )
}

describe('CampanaNotificaciones', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.notificaciones.forEach((n) => { n.leida = false })
  })

  it('muestra badge con contador de notificaciones no leídas', async () => {
    renderCampana()
    const btn = screen.getByRole('button', { name: /notificaciones/i })
    expect(btn).toBeInTheDocument()
    expect(await screen.findByText('1')).toBeInTheDocument()
  })

  it('abre panel al hacer clic y muestra notificación', async () => {
    renderCampana()
    const btn = screen.getByRole('button', { name: /notificaciones/i })
    await fireEvent.click(btn)
    await waitFor(() => expect(screen.getByText('Labial rojo stock bajo')).toBeInTheDocument())
  })

  it('marca como leída al hacer clic en notificación', async () => {
    renderCampana()
    const btn = screen.getByRole('button', { name: /notificaciones/i })
    await fireEvent.click(btn)
    const item = await screen.findByText('Labial rojo stock bajo')
    await fireEvent.click(item)
    await waitFor(() => expect(screen.queryByText('Labial rojo stock bajo')).not.toBeInTheDocument())
  })
})