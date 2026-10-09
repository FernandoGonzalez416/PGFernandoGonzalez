import { afterEach, describe, expect, it, vi } from 'vitest'
import { configurarAutenticacion } from '../api/client'
import { anularVenta, listarVentas, registrarVenta } from './ventas'

function respuestaJson(cuerpo: unknown, status = 200): Response {
  return {
    status,
    ok: status >= 200 && status < 300,
    json: async () => cuerpo,
  } as unknown as Response
}

function fetchFalso(respondedor: () => Response) {
  return vi.fn<typeof fetch>(async () => respondedor())
}

afterEach(() => {
  vi.unstubAllGlobals()
  configurarAutenticacion({ obtenerToken: async () => null, alExpirarSesion: () => {} })
})

describe('servicio de ventas', () => {
  it('lista ventas con límite y desplazamiento', async () => {
    const fetchMock = fetchFalso(() => respuestaJson([]))
    vi.stubGlobal('fetch', fetchMock)

    await listarVentas({ limite: 20, desplazamiento: 40 })

    const url = new URL(String(fetchMock.mock.calls[0][0]))
    expect(url.pathname).toBe('/api/ventas')
    expect(url.searchParams.get('limite')).toBe('20')
    expect(url.searchParams.get('desplazamiento')).toBe('40')
  })

  it('envía el cuerpo de la venta al registrarla', async () => {
    const fetchMock = fetchFalso(() => respuestaJson({ id: 'v1' }, 201))
    vi.stubGlobal('fetch', fetchMock)

    await registrarVenta({
      lineas: [{ producto_id: 'p1', cantidad: 2 }],
      descuento: '5.00',
      metodo_pago: 'efectivo',
      cliente_id: null,
    })

    const peticion = fetchMock.mock.calls[0][1]
    expect(peticion?.method).toBe('POST')
    const cuerpo = JSON.parse(String(peticion?.body)) as {
      lineas: { producto_id: string; cantidad: number }[]
      descuento: string
      metodo_pago: string
    }
    expect(cuerpo.lineas[0]).toEqual({ producto_id: 'p1', cantidad: 2 })
    expect(cuerpo.descuento).toBe('5.00')
    expect(cuerpo.metodo_pago).toBe('efectivo')
  })

  it('anula la venta indicada enviando el motivo', async () => {
    const fetchMock = fetchFalso(() => respuestaJson({ id: 'v1' }))
    vi.stubGlobal('fetch', fetchMock)

    await anularVenta('v1', { motivo_anulacion: 'Error de cobro' })

    const url = new URL(String(fetchMock.mock.calls[0][0]))
    expect(url.pathname).toBe('/api/ventas/v1/anular')
    const cuerpo = JSON.parse(String(fetchMock.mock.calls[0][1]?.body)) as {
      motivo_anulacion: string
    }
    expect(cuerpo.motivo_anulacion).toBe('Error de cobro')
  })
})
