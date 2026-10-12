import { describe, it, expect, beforeEach } from 'vitest'
import { guardarDato, leerDato, eliminarDato, hayEspacioDisponible } from './almacenamiento'

describe('almacenamiento local', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('guarda y lee un arreglo de ventas', () => {
    const ventas = [
      { client_request_id: 'a', folio_provisional: 'T-0001', total: 100 },
      { client_request_id: 'b', folio_provisional: 'T-0002', total: 200 },
    ]
    expect(guardarDato('cola_ventas', 'user1', ventas)).toEqual({ exito: true })
    const resultado = leerDato<typeof ventas>('cola_ventas', 'user1')
    expect(resultado.datos).toEqual(ventas)
  })

  it('guarda y lee un caché de catálogo', () => {
    const catalogo = [
      { id: 'p1', codigo: 'X', nombre: 'Labial', precio_venta: 50, existencia: 3 },
    ]
    expect(guardarDato('catalogo_cache', 'user1', catalogo)).toEqual({ exito: true })
    const resultado = leerDato<typeof catalogo>('catalogo_cache', 'user1')
    expect(resultado.datos).toHaveLength(1)
  })

  it('separa los datos por usuario', () => {
    guardarDato('cola_ventas', 'userA', [{ id: 1 }])
    guardarDato('cola_ventas', 'userB', [{ id: 2 }])
    expect(leerDato('cola_ventas', 'userA').datos).toEqual([{ id: 1 }])
    expect(leerDato('cola_ventas', 'userB').datos).toEqual([{ id: 2 }])
  })

  it('devuelve null cuando no hay datos', () => {
    expect(leerDato('cola_ventas', 'nadie').datos).toBeNull()
  })

  it('elimina los datos de un usuario', () => {
    guardarDato('cola_ventas', 'user1', [{ id: 1 }])
    eliminarDato('cola_ventas', 'user1')
    expect(leerDato('cola_ventas', 'user1').datos).toBeNull()
  })

  it('hayEspacioDisponible devuelve true con localStorage vacío', () => {
    expect(hayEspacioDisponible()).toBe(true)
  })
})
