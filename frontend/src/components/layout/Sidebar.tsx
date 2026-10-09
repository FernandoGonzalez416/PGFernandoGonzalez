import { NavLink } from 'react-router'
import { CAPACIDADES } from '../../api/capacidades'
import { useAuth } from '../../auth/useAuth'
import { useCan } from '../../auth/useCan'

export function Sidebar({ abierto, onNavegar }: { abierto: boolean; onNavegar: () => void }) {
  const { perfil } = useAuth()
  const puedeProductos = useCan(CAPACIDADES.productosConsultar)
  const puedeCategorias = useCan(CAPACIDADES.categoriasGestionar)
  const puedeProveedores = useCan(CAPACIDADES.proveedoresGestionar)

  const items = [
    { to: '/productos', etiqueta: 'Productos', visible: puedeProductos },
    { to: '/categorias', etiqueta: 'Categorías', visible: puedeCategorias },
    { to: '/proveedores', etiqueta: 'Proveedores', visible: puedeProveedores },
  ].filter((item) => item.visible)

  return (
    <aside className={`sidebar${abierto ? ' abierto' : ''}`}>
      <div className="brand">
        <span className="brand-mark" aria-hidden="true">FC</span>
        <span className="brand-text">
          <span className="brand-name">Familia de la Cruz</span>
          <span className="brand-sub">Inventarios y reabastecimiento</span>
        </span>
      </div>

      <nav className="nav" aria-label="Navegación principal">
        <span className="nav-group-label">Catálogo</span>
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            onClick={onNavegar}
          >
            <span className="nav-dot" aria-hidden="true" />
            {item.etiqueta}
          </NavLink>
        ))}
      </nav>

      {perfil !== null && (
        <div className="sidebar-foot">
          <div className="user-name">{perfil.nombre}</div>
          <div className="user-role">{perfil.rol}</div>
        </div>
      )}
    </aside>
  )
}
