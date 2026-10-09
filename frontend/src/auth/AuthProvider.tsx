import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { apiFetch, configurarAutenticacion } from '../api/client'
import type { MeRead } from '../api/types'
import {
  alCambiarSesion,
  cerrarSesion as cerrarSesionServicio,
  iniciarSesion as iniciarSesionServicio,
  obtenerAccessToken,
  obtenerSesionActual,
} from '../services/auth'
import { ContextoAutenticacion, type EstadoAutenticacion } from './contexto'

export function ProveedorAutenticacion({ children }: { children: ReactNode }) {
  const [perfil, setPerfil] = useState<MeRead | null>(null)
  const [cargando, setCargando] = useState(true)

  const cargarPerfil = useCallback(async () => {
    const datos = await apiFetch<MeRead>('/api/me')
    setPerfil(datos)
  }, [])

  useEffect(() => {
    configurarAutenticacion({
      obtenerToken: obtenerAccessToken,
      alExpirarSesion: async () => {
        await cerrarSesionServicio()
        setPerfil(null)
      },
    })
  }, [])

  useEffect(() => {
    let vigente = true

    obtenerSesionActual()
      .then(async (sesion) => {
        if (!vigente || !sesion) return
        try {
          await cargarPerfil()
        } catch {
          if (vigente) setPerfil(null)
        }
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    const desuscribir = alCambiarSesion((evento) => {
      if (vigente && evento === 'SIGNED_OUT') setPerfil(null)
    })

    return () => {
      vigente = false
      desuscribir()
    }
  }, [cargarPerfil])

  const iniciarSesion = useCallback(
    async (email: string, password: string) => {
      setCargando(true)
      try {
        await iniciarSesionServicio(email, password)
        await cargarPerfil()
      } finally {
        setCargando(false)
      }
    },
    [cargarPerfil],
  )

  const cerrarSesion = useCallback(async () => {
    await cerrarSesionServicio()
    setPerfil(null)
  }, [])

  const valor = useMemo<EstadoAutenticacion>(
    () => ({ perfil, cargando, iniciarSesion, cerrarSesion }),
    [perfil, cargando, iniciarSesion, cerrarSesion],
  )

  return <ContextoAutenticacion.Provider value={valor}>{children}</ContextoAutenticacion.Provider>
}
