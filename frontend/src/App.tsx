import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { CAPACIDADES } from './api/capacidades'
import { ProveedorAutenticacion } from './auth/AuthProvider'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { RequireCapacidad } from './auth/RequireCapacidad'
import { AppLayout } from './components/layout/AppLayout'
import { ToastProvider } from './components/ui/ToastProvider'
import { Categorias } from './pages/Categorias'
import { Inventario } from './pages/Inventario'
import { Login } from './pages/Login'
import { NoEncontrado } from './pages/NoEncontrado'
import { Productos } from './pages/Productos'
import { Proveedores } from './pages/Proveedores'
import { VentaDetalle } from './pages/VentaDetalle'
import { VentaNueva } from './pages/VentaNueva'
import { VentaRecibo } from './pages/VentaRecibo'
import { Ventas } from './pages/Ventas'

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <ProveedorAutenticacion>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<Navigate to="/productos" replace />} />
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
                <Route path="*" element={<NoEncontrado />} />
              </Route>
            </Route>
          </Routes>
        </ProveedorAutenticacion>
      </ToastProvider>
    </BrowserRouter>
  )
}

export default App
