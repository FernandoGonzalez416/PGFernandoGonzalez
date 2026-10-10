import { useAuth } from '../../auth/useAuth'
import { CampanaNotificaciones } from '../notificaciones/CampanaNotificaciones'

export function Topbar() {
  const { perfil, cerrarSesion } = useAuth()

  const nombre = perfil?.nombre_completo ?? perfil?.nombre_usuario ?? 'Usuario'
  const rol = perfil?.rol

  return (
    <header className="topbar">
      <button className="menu-btn" aria-label="Abrir menú">
        ☰
      </button>
      <div className="topbar-right">
        <CampanaNotificaciones />
        <div className="usuario">
          <div className="usuario-info">
            <strong>{nombre}</strong>
            <span>{rol}</span>
          </div>
          <div className="usuario-menu">
            <button className="usuario-trigger" aria-label="Menú de usuario">
              {nombre[0]?.toUpperCase() ?? 'U'}
            </button>
            <div className="menu-desplegable">
              <button onClick={cerrarSesion}>Cerrar sesión</button>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}