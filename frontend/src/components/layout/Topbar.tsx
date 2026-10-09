import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../../auth/useAuth'

function iniciales(nombre: string): string {
  const partes = nombre.trim().split(/\s+/).filter((parte) => parte !== '')
  const primera = partes[0]?.[0] ?? '?'
  const segunda = partes[1]?.[0] ?? ''
  return (primera + segunda).toUpperCase()
}

export function Topbar({ titulo, onAbrirMenu }: { titulo: string; onAbrirMenu: () => void }) {
  const { perfil, cerrarSesion } = useAuth()
  const [abierto, setAbierto] = useState(false)
  const contenedor = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!abierto) return
    const alClicFuera = (evento: MouseEvent) => {
      if (contenedor.current && !contenedor.current.contains(evento.target as Node)) {
        setAbierto(false)
      }
    }
    document.addEventListener('mousedown', alClicFuera)
    return () => document.removeEventListener('mousedown', alClicFuera)
  }, [abierto])

  const salir = async () => {
    setAbierto(false)
    await cerrarSesion()
  }

  return (
    <header className="topbar">
      <button type="button" className="menu-btn" aria-label="Abrir menú" onClick={onAbrirMenu}>
        ≡
      </button>
      <h2 className="topbar-title">{titulo}</h2>
      <div className="topbar-spacer" />
      {perfil !== null && (
        <div className="user-menu" ref={contenedor}>
          <button
            type="button"
            className="user-menu-trigger"
            aria-haspopup="menu"
            aria-expanded={abierto}
            onClick={() => setAbierto((valor) => !valor)}
          >
            <span className="avatar" aria-hidden="true">{iniciales(perfil.nombre)}</span>
            <span>{perfil.nombre}</span>
          </button>
          {abierto && (
            <div className="user-menu-panel" role="menu">
              <div className="panel-head">
                <strong>{perfil.nombre}</strong>
                <span>{perfil.email}</span>
              </div>
              <button type="button" className="menu-item" role="menuitem" onClick={salir}>
                Cerrar sesión
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  )
}
