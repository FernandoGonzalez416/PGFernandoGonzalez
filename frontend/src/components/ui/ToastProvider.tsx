import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'
import { ContextoToast, type ContextoToastValor, type NivelToast, type Notificar } from './contextoToast'

type Toast = { id: number; mensaje: string; nivel: NivelToast }

const DURACION_MS: Record<NivelToast, number> = {
  ok: 4000,
  info: 4500,
  error: 6000,
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const siguienteId = useRef(0)

  const descartar = useCallback((id: number) => {
    setToasts((actuales) => actuales.filter((toast) => toast.id !== id))
  }, [])

  const notificar = useCallback<Notificar>(
    (mensaje, nivel = 'info') => {
      const id = siguienteId.current++
      setToasts((actuales) => [...actuales, { id, mensaje, nivel }])
      window.setTimeout(() => descartar(id), DURACION_MS[nivel])
    },
    [descartar],
  )

  const valor = useMemo<ContextoToastValor>(() => ({ notificar }), [notificar])

  return (
    <ContextoToast.Provider value={valor}>
      {children}
      <div className="toast-stack" role="region" aria-live="polite" aria-label="Notificaciones">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.nivel}`} role="status">
            <p>{toast.mensaje}</p>
            <button
              type="button"
              className="toast-close"
              aria-label="Cerrar notificación"
              onClick={() => descartar(toast.id)}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </ContextoToast.Provider>
  )
}
