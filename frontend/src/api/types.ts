import type { components } from './schema'

export type MeRead = components['schemas']['MeRead']
export type ProductoRead = components['schemas']['ProductoRead']
export type ProductoCreate = components['schemas']['ProductoCreate']
export type ProductoUpdate = components['schemas']['ProductoUpdate']
export type CategoriaRead = components['schemas']['CategoriaRead']
export type CategoriaCreate = components['schemas']['CategoriaCreate']
export type CategoriaUpdate = components['schemas']['CategoriaUpdate']
export type ProveedorRead = components['schemas']['ProveedorRead']
export type ProveedorCreate = components['schemas']['ProveedorCreate']
export type ProveedorUpdate = components['schemas']['ProveedorUpdate']
export type ExistenciaRead = components['schemas']['ExistenciaRead']

export type Capacidad = MeRead['capacidades'][number]
export type Rol = MeRead['rol']
