import { describe, expect, it } from 'vitest'
import { crearProducto } from '../test/fixtures'
import {
  aCentavos,
  agregarLinea,
  cambiarCantidad,
  cantidadDisponible,
  centavosAQ,
  quitarLinea,
  totalesCarrito,
  type LineaCarrito,
} from './carrito'

function linea(overrides: Partial<LineaCarrito> = {}): LineaCarrito {
  return {
    productoId: 'prod-1',
    codigo: 'SIM-001',
    nombre: 'Producto de prueba',
    precioUnitarioCents: 2500,
    cantidad: 1,
    existenciaDisponible: 10,
    ...overrides,
  }
}

describe('aCentavos', () => {
  it('convierte montos a centavos enteros', () => {
    expect(aCentavos('25.00')).toBe(2500)
    expect(aCentavos('0.1')).toBe(10)
    expect(aCentavos(25)).toBe(2500)
  })

  it('redondea hacia arriba el tercer decimal (medio centavo)', () => {
    expect(aCentavos('12.505')).toBe(1251)
    expect(aCentavos('12.504')).toBe(1250)
  })

  it('devuelve 0 para valores vacíos o inválidos', () => {
    expect(aCentavos(null)).toBe(0)
    expect(aCentavos(undefined)).toBe(0)
    expect(aCentavos('')).toBe(0)
    expect(aCentavos('abc')).toBe(0)
  })
})

describe('centavosAQ', () => {
  it('formatea centavos como cadena decimal', () => {
    expect(centavosAQ(2500)).toBe('25.00')
    expect(centavosAQ(1251)).toBe('12.51')
  })
})

describe('totalesCarrito', () => {
  it('calcula subtotal, descuento y total en centavos', () => {
    const totales = totalesCarrito([linea({ cantidad: 3 })], 500)
    expect(totales).toEqual({ subtotalCents: 7500, descuentoCents: 500, totalCents: 7000 })
  })

  it('limita el descuento al subtotal y descarta negativos', () => {
    expect(totalesCarrito([linea({ cantidad: 2 })], 99999).descuentoCents).toBe(5000)
    expect(totalesCarrito([linea({ cantidad: 2 })], -100).descuentoCents).toBe(0)
  })
})

describe('agregarLinea', () => {
  it('agrega un producto nuevo y no supera la existencia', () => {
    const producto = crearProducto({ existencia: '2.00' })
    const primera = agregarLinea([], producto)
    expect(primera).toHaveLength(1)
    expect(primera[0].cantidad).toBe(1)

    const segunda = agregarLinea(primera, producto)
    const tercera = agregarLinea(segunda, producto)
    expect(tercera[0].cantidad).toBe(2)
  })

  it('no agrega productos sin existencia', () => {
    expect(agregarLinea([], crearProducto({ existencia: '0.00' }))).toHaveLength(0)
  })

  it('combina líneas del mismo producto', () => {
    const producto = crearProducto({ id: 'prod-1', existencia: '10.00' })
    const resultado = agregarLinea(agregarLinea([], producto), producto)
    expect(resultado).toHaveLength(1)
    expect(resultado[0].cantidad).toBe(2)
  })
})

describe('cantidadDisponible', () => {
  it('trunca a entero la existencia', () => {
    expect(cantidadDisponible(crearProducto({ existencia: '2.90' }))).toBe(2)
    expect(cantidadDisponible(crearProducto({ existencia: '0.00' }))).toBe(0)
  })
})

describe('cambiarCantidad', () => {
  it('mantiene la cantidad entre 1 y la existencia disponible', () => {
    expect(cambiarCantidad([linea({ existenciaDisponible: 5 })], 'prod-1', 0)[0].cantidad).toBe(1)
    expect(cambiarCantidad([linea({ existenciaDisponible: 5 })], 'prod-1', 99)[0].cantidad).toBe(5)
    expect(cambiarCantidad([linea({ existenciaDisponible: 5 })], 'prod-1', 3)[0].cantidad).toBe(3)
  })
})

describe('quitarLinea', () => {
  it('elimina la línea indicada', () => {
    const resultado = quitarLinea([linea({ productoId: 'a' }), linea({ productoId: 'b' })], 'a')
    expect(resultado).toHaveLength(1)
    expect(resultado[0].productoId).toBe('b')
  })
})
