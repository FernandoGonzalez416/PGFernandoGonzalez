import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'
import { crearPerfil } from '../test/fixtures'
import { ContextoAutenticacion, type EstadoAutenticacion } from './contexto'
import { RequireCapacidad } from './RequireCapacidad'

function montarCon(perfil: EstadoAutenticacion['perfil']) {
  const valor: EstadoAutenticacion = {
    perfil,
    cargando: false,
    iniciarSesion: async () => {},
    cerrarSesion: async () => {},
  }
  return render(
    <MemoryRouter>
      <ContextoAutenticacion.Provider value={valor}>
        <RequireCapacidad capacidad="categorias:gestionar">
          <p>contenido protegido</p>
        </RequireCapacidad>
      </ContextoAutenticacion.Provider>
    </MemoryRouter>,
  )
}

describe('RequireCapacidad', () => {
  it('renderiza el contenido cuando el perfil tiene la capacidad', () => {
    montarCon(crearPerfil('propietario', ['categorias:gestionar']))
    expect(screen.getByText('contenido protegido')).toBeInTheDocument()
  })

  it('muestra la vista 403 cuando falta la capacidad', () => {
    montarCon(crearPerfil('padre', ['productos:consultar']))
    expect(screen.getByText('No tienes acceso a esta sección')).toBeInTheDocument()
    expect(screen.queryByText('contenido protegido')).not.toBeInTheDocument()
  })
})
