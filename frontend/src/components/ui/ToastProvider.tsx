import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'
import { X } from 'lucide-react'
import { ContextoToast, type ContextoToastValor, type NivelToast, type Notificar } from './contextoToast'

type Toast = { id: number; mensaje: string; nivel: NivelToast }

const DURACION_MS: Record<NivelToast, number> = {
  ok: 4000,
  info: 4500,
  error: 6000,
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const idActual = useRef(0)

  const descartar = useCallback((id: number) => {
    setToasts((actuales) => actuales.filter((t) => t.id !== id))
  }, [])

  const notificar = useCallback<Notificar>(
    (mensaje, nivel = 'info') => {
      const id = ++idActual.current
      setToasts((actuales) => [...actuales, { id, mensaje, nivel }])
      const timeout = setTimeout(() => descartar(id), DURACION_MS[nivel])
      return () => clearTimeout(timeout)
    },
    [descartar],
  )

  const valor = useMemo<ContextoToastValor>(
    () => ({
      notificar,
      exito: (mensaje: string) => notificar(mensaje, 'ok'),
      error: (mensaje: string) => notificar(mensaje, 'error'),
      info: (mensaje: string) => notificar(mensaje, 'info'),
    }),
    [notificar],
  )

  return (
    <ContextoToast.Provider value={valor}>
      {children}
      <div className="toast-contenedor" aria-live="polite" aria-label="Notificaciones">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.nivel}`}>
            <p>{toast.mensaje}</p>
            <button
              type="button"
              className="toast-close"
              aria-label="Cerrar notificación"
              onClick={() => descartar(toast.id)}
            >
              <X aria-hidden="true" />
            </button>
          </div>
        ))}
      </div>
    </ContextoToast.Provider>
  )
}

export { useToast } from './useToast'