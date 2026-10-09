import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import { CAPACIDADES } from './api/capacidades'
import { ProveedorAutenticacion } from './auth/AuthProvider'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { RequireCapacidad } from './auth/RequireCapacidad'
import { AppLayout } from './components/layout/AppLayout'
import { ToastProvider } from './components/ui/ToastProvider'
import { Categorias } from './pages/Categorias'
import { Login } from './pages/Login'
import { NoEncontrado } from './pages/NoEncontrado'
import { Productos } from './pages/Productos'
import { Proveedores } from './pages/Proveedores'

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
