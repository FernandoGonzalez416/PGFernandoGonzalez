import { useState, useEffect, useCallback } from 'react'

/**
 * Estado de conexión del navegador (P27/F5).
 *
 * `navigator.onLine` no es infalible (dice "online" con wifi sin salida), por
 * eso `marcarOffline` permite que la capa que detecta un fallo real de red
 * baje el indicador hasta que el navegador vuelva a emitir `online`.
 */
export function useConexion(): { online: boolean; marcarOffline: () => void } {
  const [online, setOnline] = useState<boolean>(navigator.onLine)

  const alVolver = useCallback(() => setOnline(true), [])
  const alPerder = useCallback(() => setOnline(false), [])

  useEffect(() => {
    window.addEventListener('online', alVolver)
    window.addEventListener('offline', alPerder)
    return () => {
      window.removeEventListener('online', alVolver)
      window.removeEventListener('offline', alPerder)
    }
  }, [alVolver, alPerder])

  const marcarOffline = useCallback(() => setOnline(false), [])

  return { online, marcarOffline }
}
