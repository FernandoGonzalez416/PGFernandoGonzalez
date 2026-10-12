import { BrowserRouter, Route, Routes } from 'react-router'
import { CAPACIDADES } from './api/capacidades'
import { ProveedorAutenticacion } from './auth/AuthProvider'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { RequireCapacidad } from './auth/RequireCapacidad'
import { AppLayout } from './components/layout/AppLayout'
import { ToastProvider } from './components/ui/ToastProvider'
import { Suspense, lazy } from 'react'
import ErrorBoundary from './components/ErrorBoundary'
import { NoEncontrado } from './pages/NoEncontrado'
import { Login } from './pages/Login'
import { VentasPendientes } from './pages/VentasPendientes'
import { ProveedorOffline } from './offline/ProveedorOffline'

const Panel = lazy(() => import('./pages/Panel').then((m) => ({ default: m.Panel })))
const Productos = lazy(() => import('./pages/Productos').then((m) => ({ default: m.Productos })))
const Ventas = lazy(() => import('./pages/Ventas').then((m) => ({ default: m.Ventas })))
const VentaDetalle = lazy(() => import('./pages/VentaDetalle').then((m) => ({ default: m.VentaDetalle })))
const VentaNueva = lazy(() => import('./pages/VentaNueva').then((m) => ({ default: m.VentaNueva })))
const VentaRecibo = lazy(() => import('./pages/VentaRecibo').then((m) => ({ default: m.VentaRecibo })))
const Inventario = lazy(() => import('./pages/Inventario').then((m) => ({ default: m.Inventario })))
const Categorias = lazy(() => import('./pages/Categorias').then((m) => ({ default: m.Categorias })))
const Proveedores = lazy(() => import('./pages/Proveedores').then((m) => ({ default: m.Proveedores })))
const Alertas = lazy(() => import('./pages/Alertas').then((m) => ({ default: m.Alertas })))
const Reportes = lazy(() => import('./pages/Reportes').then((m) => ({ default: m.Reportes })))
const Sugerencias = lazy(() => import('./pages/Sugerencias').then((m) => ({ default: m.Sugerencias })))
const Notificaciones = lazy(() => import('./pages/Notificaciones').then((m) => ({ default: m.Notificaciones })))
const Predicciones = lazy(() => import('./pages/Predicciones').then((m) => ({ default: m.Predicciones })))

function Fallback() {
  return <div className="pagina">Cargando...</div>
}

function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <ToastProvider>
          <ProveedorAutenticacion>
            <ProveedorOffline>
              <Suspense fallback={<Fallback />}>
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route element={<ProtectedRoute />}>
                    <Route element={<AppLayout />}>
                      <Route path="/" element={<Panel />} />
                      <Route path="/productos" element={<Productos />} />
                      <Route
                        path="/ventas/nueva"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.ventasRegistrar}>
                            <VentaNueva />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/ventas/pendientes"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.ventasRegistrar}>
                            <VentasPendientes />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/ventas"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.stockConsultar}>
                            <Ventas />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/ventas/:id"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.stockConsultar}>
                            <VentaDetalle />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/ventas/:id/recibo"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.stockConsultar}>
                            <VentaRecibo />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/inventario"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.stockConsultar}>
                            <Inventario />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/categorias"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.categoriasGestionar}>
                            <Categorias />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/proveedores"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.proveedoresGestionar}>
                            <Proveedores />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/alertas"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.alertasVer}>
                            <Alertas />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/reportes"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.reportesVer}>
                            <Reportes />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/sugerencias"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.sugerenciasVer}>
                            <Sugerencias />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/notificaciones"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.alertasVer}>
                            <Notificaciones />
                          </RequireCapacidad>
                        }
                      />
                      <Route
                        path="/predicciones"
                        element={
                          <RequireCapacidad capacidad={CAPACIDADES.prediccionVer}>
                            <Predicciones />
                          </RequireCapacidad>
                        }
                      />
                      <Route path="*" element={<NoEncontrado />} />
                    </Route>
                  </Route>
                </Routes>
              </Suspense>
            </ProveedorOffline>
          </ProveedorAutenticacion>
        </ToastProvider>
      </ErrorBoundary>
    </BrowserRouter>
  )
}

export default App