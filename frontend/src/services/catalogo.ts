import { apiFetch } from '../api/client'
import type {
  CategoriaCreate,
  CategoriaRead,
  CategoriaUpdate,
  ExistenciaRead,
  ProductoCreate,
  ProductoRead,
  ProductoUpdate,
  ProveedorCreate,
  ProveedorRead,
  ProveedorUpdate,
} from '../api/types'

export type FiltrosProductos = {
  q?: string
  categoriaId?: string | null
  incluirInactivos?: boolean
  limite?: number
  desplazamiento?: number
}

function construirConsulta(parametros: Record<string, string | number | boolean | null | undefined>): string {
  const busqueda = new URLSearchParams()
  for (const [clave, valor] of Object.entries(parametros)) {
    if (valor === null || valor === undefined || valor === '' || valor === false) continue
    busqueda.set(clave, String(valor))
  }
  const cadena = busqueda.toString()
  return cadena === '' ? '' : `?${cadena}`
}

export function listarProductos(filtros: FiltrosProductos = {}): Promise<ProductoRead[]> {
  const consulta = construirConsulta({
    q: filtros.q,
    categoria_id: filtros.categoriaId,
    incluir_inactivos: filtros.incluirInactivos,
    limite: filtros.limite,
    desplazamiento: filtros.desplazamiento,
  })
  return apiFetch<ProductoRead[]>(`/api/productos${consulta}`)
}

export function crearProducto(datos: ProductoCreate): Promise<ProductoRead> {
  return apiFetch<ProductoRead>('/api/productos', {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

export function actualizarProducto(productoId: string, datos: ProductoUpdate): Promise<ProductoRead> {
  return apiFetch<ProductoRead>(`/api/productos/${productoId}`, {
    method: 'PATCH',
    body: JSON.stringify(datos),
  })
}

export function listarExistenciasDeProducto(productoId: string): Promise<ExistenciaRead[]> {
  return apiFetch<ExistenciaRead[]>(`/api/productos/${productoId}/existencia`)
}

export function listarCategorias(incluirInactivas = false): Promise<CategoriaRead[]> {
  const consulta = construirConsulta({ incluir_inactivas: incluirInactivas })
  return apiFetch<CategoriaRead[]>(`/api/categorias${consulta}`)
}

export function crearCategoria(datos: CategoriaCreate): Promise<CategoriaRead> {
  return apiFetch<CategoriaRead>('/api/categorias', {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

export function actualizarCategoria(
  categoriaId: string,
  datos: CategoriaUpdate,
): Promise<CategoriaRead> {
  return apiFetch<CategoriaRead>(`/api/categorias/${categoriaId}`, {
    method: 'PATCH',
    body: JSON.stringify(datos),
  })
}

export function listarProveedores(incluirInactivos = false): Promise<ProveedorRead[]> {
  const consulta = construirConsulta({ incluir_inactivos: incluirInactivos })
  return apiFetch<ProveedorRead[]>(`/api/proveedores${consulta}`)
}

export function crearProveedor(datos: ProveedorCreate): Promise<ProveedorRead> {
  return apiFetch<ProveedorRead>('/api/proveedores', {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

export function actualizarProveedor(
  proveedorId: string,
  datos: ProveedorUpdate,
): Promise<ProveedorRead> {
  return apiFetch<ProveedorRead>(`/api/proveedores/${proveedorId}`, {
    method: 'PATCH',
    body: JSON.stringify(datos),
  })
}
