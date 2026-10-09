import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { Login } from './Login'

const mocks = vi.hoisted(() => ({ iniciarSesion: vi.fn() }))

vi.mock('../auth/useAuth', () => ({
  useAuth: () => ({
    perfil: null,
    cargando: false,
    iniciarSesion: mocks.iniciarSesion,
    cerrarSesion: vi.fn(),
  }),
}))

function montar() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>,
  )
}

function completar(correo: string, contrasena: string) {
  fireEvent.change(screen.getByLabelText('Correo electrónico'), { target: { value: correo } })
  fireEvent.change(screen.getByLabelText('Contraseña'), { target: { value: contrasena } })
}

beforeEach(() => {
  mocks.iniciarSesion.mockReset()
})

describe('Login', () => {
  it('envía el correo y la contraseña al iniciar sesión', async () => {
    mocks.iniciarSesion.mockResolvedValue(undefined)
    montar()
    completar('dueno@correo.com', '123456')
    fireEvent.click(screen.getByRole('button', { name: 'Ingresar' }))
    await waitFor(() => expect(mocks.iniciarSesion).toHaveBeenCalledWith('dueno@correo.com', '123456'))
  })

  it('exige correo y contraseña antes de enviar', async () => {
    montar()
    fireEvent.click(screen.getByRole('button', { name: 'Ingresar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Ingresa tu correo y tu contraseña.')
    expect(mocks.iniciarSesion).not.toHaveBeenCalled()
  })

  it('muestra el error cuando las credenciales fallan', async () => {
    mocks.iniciarSesion.mockRejectedValueOnce(new Error('Correo o contraseña incorrectos.'))
    montar()
    completar('dueno@correo.com', 'mala')
    fireEvent.click(screen.getByRole('button', { name: 'Ingresar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Correo o contraseña incorrectos.')
  })
})
