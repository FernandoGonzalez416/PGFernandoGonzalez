import { Navigate, Outlet } from 'react-router'
import { PantallaCargando } from '../components/ui/PantallaCargando'
import { useAuth } from './useAuth'

export function ProtectedRoute() {
  const { perfil, cargando } = useAuth()

  if (cargando) return <PantallaCargando mensaje="Verificando tu sesión…" />
  if (!perfil) return <Navigate to="/login" replace />

  return <Outlet />
}
