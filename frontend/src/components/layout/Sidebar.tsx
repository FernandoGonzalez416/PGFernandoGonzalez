import { NavLink } from 'react-router'
import {
  BarChart3,
  Bell,
  BellRing,
  Boxes,
  Clock,
  LayoutDashboard,
  Lightbulb,
  Package,
  Receipt,
  ShoppingCart,
  Tags,
  TrendingUp,
  Truck,
  type LucideIcon,
} from 'lucide-react'
import { CAPACIDADES } from '../../api/capacidades'
import { useAuth } from '../../auth/useAuth'
import { useCan } from '../../auth/useCan'

type ItemNav = { to: string; etiqueta: string; visible: boolean; end?: boolean; icono: LucideIcon }

export function Sidebar({ abierto, onNavegar }: { abierto: boolean; onNavegar: () => void }) {
  const { perfil } = useAuth()
  const puedeProductos = useCan(CAPACIDADES.productosConsultar)
  const puedeCategorias = useCan(CAPACIDADES.categoriasGestionar)
  const puedeProveedores = useCan(CAPACIDADES.proveedoresGestionar)
  const puedeVentasRegistrar = useCan(CAPACIDADES.ventasRegistrar)
  const puedeStockConsultar = useCan(CAPACIDADES.stockConsultar)
  const puedeAlertas = useCan(CAPACIDADES.alertasVer)
  const puedeReportes = useCan(CAPACIDADES.reportesVer)
  const puedeSugerencias = useCan(CAPACIDADES.sugerenciasVer)
  const puedePredicciones = useCan(CAPACIDADES.prediccionVer)

  const grupos: { etiqueta: string; items: ItemNav[] }[] = [
    {
      etiqueta: 'Inicio',
      items: [
        { to: '/', etiqueta: 'Panel', visible: true, end: true, icono: LayoutDashboard },
      ],
    },
    {
      etiqueta: 'Catálogo',
      items: [
        { to: '/productos', etiqueta: 'Productos', visible: puedeProductos, icono: Package },
        { to: '/categorias', etiqueta: 'Categorías', visible: puedeCategorias, icono: Tags },
        { to: '/proveedores', etiqueta: 'Proveedores', visible: puedeProveedores, icono: Truck },
      ],
    },
    {
      etiqueta: 'Ventas',
      items: [
        { to: '/ventas/nueva', etiqueta: 'Nueva venta', visible: puedeVentasRegistrar, icono: ShoppingCart },
        { to: '/ventas/pendientes', etiqueta: 'Ventas pendientes', visible: puedeVentasRegistrar, icono: Clock },
        { to: '/ventas', etiqueta: 'Historial', visible: puedeStockConsultar, end: true, icono: Receipt },
      ],
    },
    {
      etiqueta: 'Inventario',
      items: [{ to: '/inventario', etiqueta: 'Inventario', visible: puedeStockConsultar, icono: Boxes }],
    },
    {
      etiqueta: 'Análisis',
      items: [
        { to: '/alertas', etiqueta: 'Alertas', visible: puedeAlertas, icono: BellRing },
        { to: '/reportes', etiqueta: 'Reportes', visible: puedeReportes, icono: BarChart3 },
        { to: '/sugerencias', etiqueta: 'Sugerencias de compra', visible: puedeSugerencias, icono: Lightbulb },
        { to: '/predicciones', etiqueta: 'Predicción de demanda', visible: puedePredicciones, icono: TrendingUp },
        { to: '/notificaciones', etiqueta: 'Notificaciones', visible: puedeAlertas, icono: Bell },
      ],
    },
  ]
    .map((grupo) => ({
      etiqueta: grupo.etiqueta,
      items: grupo.items.filter((item: ItemNav) => item.visible),
    }))
    .filter((grupo) => grupo.items.length > 0)

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
        {grupos.map((grupo) => (
          <div key={grupo.etiqueta} className="nav-group">
            <span className="nav-group-label">{grupo.etiqueta}</span>
            {grupo.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
                onClick={onNavegar}
              >
                <span className="nav-icono" aria-hidden="true">
                  <item.icono />
                </span>
                {item.etiqueta}
              </NavLink>
            ))}
          </div>
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
