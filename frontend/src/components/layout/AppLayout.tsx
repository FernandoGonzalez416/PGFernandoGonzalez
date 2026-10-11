import { useState } from 'react'
import { Outlet, useLocation } from 'react-router'
import { BarraDemo } from './BarraDemo'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'

const TITULOS: Record<string, string> = {
  '/': 'Panel',
  '/productos': 'Productos',
  '/categorias': 'Categorías',
  '/proveedores': 'Proveedores',
  '/ventas': 'Ventas',
  '/ventas/nueva': 'Nueva venta',
  '/inventario': 'Inventario',
  '/alertas': 'Alertas',
  '/reportes': 'Reportes',
  '/sugerencias': 'Sugerencias de compra',
  '/notificaciones': 'Notificaciones',
}

function tituloDeRuta(pathname: string): string {
  if (pathname.startsWith('/ventas/nueva')) return 'Nueva venta'
  if (pathname.endsWith('/recibo')) return 'Recibo'
  if (pathname.startsWith('/ventas/')) return 'Detalle de venta'
  return TITULOS[pathname] ?? 'Panel'
}

export function AppLayout() {
  const [menuAbierto, setMenuAbierto] = useState(false)
  const { pathname } = useLocation()
  void tituloDeRuta(pathname)

  return (
    <div className="app-shell">
      <Sidebar abierto={menuAbierto} onNavegar={() => setMenuAbierto(false)} />
      {menuAbierto && (
        <div className="scrim" role="presentation" onClick={() => setMenuAbierto(false)} />
      )}
      <div className="main-column">
        <Topbar />
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
