import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { crearPerfil } from '../test/fixtures'
import { ContextoAutenticacion, type EstadoAutenticacion } from './contexto'
import { useCan } from './useCan'

const CAPACIDAD = 'productos:editar'

function Sonda() {
  const puede = useCan(CAPACIDAD)
  return <span>{puede ? 'permitido' : 'denegado'}</span>
}

function montarCon(perfil: EstadoAutenticacion['perfil']) {
  const valor: EstadoAutenticacion = {
    perfil,
    cargando: false,
    iniciarSesion: async () => {},
    cerrarSesion: async () => {},
  }
  return render(
    <ContextoAutenticacion.Provider value={valor}>
      <Sonda />
    </ContextoAutenticacion.Provider>,
  )
}

describe('useCan', () => {
  it('permite cuando el perfil tiene la capacidad', () => {
    montarCon(crearPerfil('propietario', ['productos:consultar', CAPACIDAD]))
    expect(screen.getByText('permitido')).toBeInTheDocument()
  })

  it('deniega cuando el perfil no tiene la capacidad', () => {
    montarCon(crearPerfil('padre', ['productos:consultar']))
    expect(screen.getByText('denegado')).toBeInTheDocument()
  })

  it('deniega sin perfil', () => {
    montarCon(null)
    expect(screen.getByText('denegado')).toBeInTheDocument()
  })
})
