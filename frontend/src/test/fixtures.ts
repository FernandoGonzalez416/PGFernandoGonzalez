import type { MeRead, ProductoRead } from '../api/types'

export function crearPerfil(rol: string, capacidades: string[]): MeRead {
  return {
    id: 'usuario-1',
    auth_id: 'auth-1',
    nombre: 'Usuario de prueba',
    email: 'prueba@correo.com',
    rol,
    activo: true,
    capacidades,
  }
}

export function crearProducto(overrides: Partial<ProductoRead> = {}): ProductoRead {
  return {
    id: 'prod-1',
    codigo: 'SIM-001',
    nombre: 'Producto de prueba',
    descripcion: null,
    categoria_id: 'cat-1',
    proveedor_id: null,
    precio_venta: '25.00',
    precio_costo: '12.00',
    unidad_medida: 'unidad',
    umbral_minimo: '3',
    dias_vencimiento_aviso: 30,
    fecha_vencimiento: null,
    fecha_ingreso: null,
    activo: true,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    existencia: '10.00',
    ...overrides,
  }
}
