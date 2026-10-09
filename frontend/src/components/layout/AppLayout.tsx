import { useState } from 'react'
import { Outlet, useLocation } from 'react-router'
import { BarraDemo } from './BarraDemo'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

const TITULOS: Record<string, string> = {
  '/productos': 'Productos',
  '/categorias': 'Categorías',
  '/proveedores': 'Proveedores',
}

export function AppLayout() {
  const [menuAbierto, setMenuAbierto] = useState(false)
  const { pathname } = useLocation()
  const titulo = TITULOS[pathname] ?? 'Panel'

  return (
    <div className="app-shell">
      <Sidebar abierto={menuAbierto} onNavegar={() => setMenuAbierto(false)} />
      {menuAbierto && (
        <div className="scrim" role="presentation" onClick={() => setMenuAbierto(false)} />
      )}
      <div className="main-column">
        <Topbar titulo={titulo} onAbrirMenu={() => setMenuAbierto(true)} />
        <main className="content">
          <div className="content-inner">
            <BarraDemo />
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
