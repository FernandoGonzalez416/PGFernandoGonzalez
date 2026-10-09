import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiFetch, configurarAutenticacion } from './client'

function respuesta(cuerpo: unknown, status: number): Response {
  return {
    status,
    ok: status >= 200 && status < 300,
    json: async () => cuerpo,
  } as unknown as Response
}

function respuestaSinCuerpo(status: number): Response {
  return {
    status,
    ok: status >= 200 && status < 300,
    json: async () => {
      throw new Error('sin cuerpo')
    },
  } as unknown as Response
}

function fetchFalso(respondedor: () => Response) {
  return vi.fn<typeof fetch>(async () => respondedor())
}

afterEach(() => {
  vi.unstubAllGlobals()
  configurarAutenticacion({ obtenerToken: async () => null, alExpirarSesion: () => {} })
})

describe('apiFetch', () => {
  it('adjunta el token Bearer cuando hay sesión', async () => {
    const fetchMock = fetchFalso(() => respuesta({ ok: true }, 200))
    vi.stubGlobal('fetch', fetchMock)
    configurarAutenticacion({ obtenerToken: async () => 'token-123', alExpirarSesion: () => {} })

    await apiFetch('/api/productos')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, opciones] = fetchMock.mock.calls[0]
    expect(String(url)).toContain('/api/productos')
    const cabeceras = opciones?.headers as Headers
    expect(cabeceras.get('Authorization')).toBe('Bearer token-123')
  })

  it('devuelve el cuerpo tipado en una respuesta exitosa', async () => {
    vi.stubGlobal('fetch', fetchFalso(() => respuesta({ total: 3 }, 200)))
    const datos = await apiFetch<{ total: number }>('/api/productos')
    expect(datos.total).toBe(3)
  })

  it('traduce el 403 cuando no hay mensaje del backend', async () => {
    vi.stubGlobal('fetch', fetchFalso(() => respuestaSinCuerpo(403)))
    await expect(apiFetch('/api/productos')).rejects.toMatchObject({
      status: 403,
      message: 'No tienes permiso para realizar esta acción.',
    })
  })

  it('propaga el mensaje del backend en un 409', async () => {
    vi.stubGlobal(
      'fetch',
      fetchFalso(() => respuesta({ detail: 'El producto tiene existencias.' }, 409)),
    )
    await expect(apiFetch('/api/productos/x')).rejects.toThrow('El producto tiene existencias.')
  })

  it('describe un error de validación 422 con el campo', async () => {
    vi.stubGlobal(
      'fetch',
      fetchFalso(() =>
        respuesta({ detail: [{ loc: ['body', 'nombre'], msg: 'field required', type: 'missing' }] }, 422),
      ),
    )
    await expect(apiFetch('/api/productos')).rejects.toMatchObject({
      status: 422,
      message: 'El valor de «nombre» no es válido.',
    })
  })

  it('cierra la sesión y falla cuando la respuesta es 401', async () => {
    const alExpirarSesion = vi.fn()
    vi.stubGlobal('fetch', fetchFalso(() => respuestaSinCuerpo(401)))
    configurarAutenticacion({ obtenerToken: async () => 'expirado', alExpirarSesion })

    await expect(apiFetch('/api/me')).rejects.toBeInstanceOf(ApiError)
    expect(alExpirarSesion).toHaveBeenCalledTimes(1)
  })
})
