import { afterEach, describe, expect, it, vi } from 'vitest'
import { configurarAutenticacion } from '../api/client'
import { crearProducto, listarCategorias, listarProductos } from './catalogo'

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

describe('servicio de catálogo', () => {
  it('construye la consulta de productos con los filtros', async () => {
    const fetchMock = fetchFalso(() => respuestaJson([]))
    vi.stubGlobal('fetch', fetchMock)

    await listarProductos({ q: 'labial', categoriaId: 'cat-1', incluirInactivos: true })

    const url = new URL(String(fetchMock.mock.calls[0][0]))
    expect(url.pathname).toBe('/api/productos')
    expect(url.searchParams.get('q')).toBe('labial')
    expect(url.searchParams.get('categoria_id')).toBe('cat-1')
    expect(url.searchParams.get('incluir_inactivos')).toBe('true')
  })

  it('omite los filtros vacíos', async () => {
    const fetchMock = fetchFalso(() => respuestaJson([]))
    vi.stubGlobal('fetch', fetchMock)

    await listarProductos({ q: undefined, categoriaId: null, incluirInactivos: false })

    const url = new URL(String(fetchMock.mock.calls[0][0]))
    expect(url.searchParams.has('q')).toBe(false)
    expect(url.searchParams.has('categoria_id')).toBe(false)
    expect(url.searchParams.has('incluir_inactivos')).toBe(false)
  })

  it('envía el cuerpo JSON al crear un producto', async () => {
    const fetchMock = fetchFalso(() => respuestaJson({ id: 'p1' }, 201))
    vi.stubGlobal('fetch', fetchMock)

    await crearProducto({
      codigo: 'LAB-001',
      nombre: 'Labial mate',
      categoria_id: 'cat-1',
      precio_venta: '25.00',
      precio_costo: '12.00',
      unidad_medida: 'unidad',
      umbral_minimo: '3',
      dias_vencimiento_aviso: 30,
      cantidad_inicial: '10',
    })

    const peticion = fetchMock.mock.calls[0][1]
    expect(peticion?.method).toBe('POST')
    const cuerpo = JSON.parse(String(peticion?.body)) as { codigo: string }
    expect(cuerpo.codigo).toBe('LAB-001')
  })

  it('lista categorías sin parámetros cuando no se piden inactivas', async () => {
    const fetchMock = fetchFalso(() => respuestaJson([]))
    vi.stubGlobal('fetch', fetchMock)

    await listarCategorias()

    const url = new URL(String(fetchMock.mock.calls[0][0]))
    expect(url.pathname).toBe('/api/categorias')
    expect(url.search).toBe('')
  })
})
