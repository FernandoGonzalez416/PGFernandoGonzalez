import { parseDecimal } from './format'

/**
 * Datos mínimos que el carrito necesita de un producto. Lo cumplen tanto
 * `ProductoRead` (API, valores como string) como `ProductoCache` (offline,
 * valores numéricos), por eso se tipa de forma estructural y no con uno solo.
 */
export type ProductoVendible = {
  id: string
  codigo: string
  nombre: string
  precio_venta: string | number
  existencia: string | number
}

export type LineaCarrito = {
  productoId: string
  codigo: string
  nombre: string
  precioUnitarioCents: number
  cantidad: number
  existenciaDisponible: number
}

export type TotalesCarrito = {
  subtotalCents: number
  descuentoCents: number
  totalCents: number
}

export function aCentavos(valor: string | number | null | undefined): number {
  if (valor === null || valor === undefined) return 0
  if (typeof valor === 'number') {
    return Number.isFinite(valor) ? Math.round(valor * 100) : 0
  }
  const limpio = valor.trim()
  if (!/^-?\d+(\.\d+)?$/.test(limpio)) return 0
  const negativo = limpio.startsWith('-')
  const sinSigno = negativo ? limpio.slice(1) : limpio
  const [entero, decimales = ''] = sinSigno.split('.')
  const dosDecimales = (decimales + '00').slice(0, 2)
  let cents = Number(entero) * 100 + Number(dosDecimales)
  if (Number(decimales.charAt(2) || '0') >= 5) cents += 1
  return negativo ? -cents : cents
}

export function centavosAQ(cents: number): string {
  return (cents / 100).toFixed(2)
}

export function totalesCarrito(lineas: LineaCarrito[], descuentoCents: number): TotalesCarrito {
  const subtotalCents = lineas.reduce(
    (total, linea) => total + linea.precioUnitarioCents * linea.cantidad,
    0,
  )
  const descuento = Math.min(Math.max(descuentoCents, 0), subtotalCents)
  return { subtotalCents, descuentoCents: descuento, totalCents: subtotalCents - descuento }
}

export function cantidadDisponible(producto: ProductoVendible): number {
  return Math.max(0, Math.floor(parseDecimal(producto.existencia) ?? 0))
}

export function agregarLinea(
  lineas: LineaCarrito[],
  producto: ProductoVendible,
  cantidad = 1,
): LineaCarrito[] {
  const existenciaDisponible = cantidadDisponible(producto)
  if (existenciaDisponible <= 0) return lineas

  const existente = lineas.find((linea) => linea.productoId === producto.id)
  if (existente === undefined) {
    return [
      ...lineas,
      {
        productoId: producto.id,
        codigo: producto.codigo,
        nombre: producto.nombre,
        precioUnitarioCents: aCentavos(producto.precio_venta),
        cantidad: Math.min(cantidad, existenciaDisponible),
        existenciaDisponible,
      },
    ]
  }

  return lineas.map((linea) =>
    linea.productoId === producto.id
      ? {
          ...linea,
          existenciaDisponible,
          cantidad: Math.min(linea.cantidad + cantidad, existenciaDisponible),
        }
      : linea,
  )
}

export function cambiarCantidad(
  lineas: LineaCarrito[],
  productoId: string,
  cantidad: number,
): LineaCarrito[] {
  return lineas.map((linea) =>
    linea.productoId === productoId
      ? {
          ...linea,
          cantidad: Math.min(Math.max(1, Math.trunc(cantidad)), Math.max(1, linea.existenciaDisponible)),
        }
      : linea,
  )
}

export function quitarLinea(lineas: LineaCarrito[], productoId: string): LineaCarrito[] {
  return lineas.filter((linea) => linea.productoId !== productoId)
}
