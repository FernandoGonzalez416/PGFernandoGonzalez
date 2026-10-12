import { WifiOff, CloudUpload, CheckCircle2, Clock } from 'lucide-react'

interface BarraConexionProps {
  online: boolean
  sincronizando: boolean
  pendientes: number
}

/**
 * Indicador de estado de conexión en la barra superior (P27/F5).
 * Muestra: "Sin conexión", "N pendientes", "Sincronizando…" o "Al día".
 */
export function BarraConexion({ online, sincronizando, pendientes }: BarraConexionProps) {
  if (!online) {
    return (
      <span className="pill pill-danger" role="status">
        <WifiOff aria-hidden="true" size={14} />
        Sin conexión{pendientes > 0 ? ` — ${pendientes} pendiente${pendientes !== 1 ? 's' : ''}` : ''}
      </span>
    )
  }
  if (sincronizando) {
    return (
      <span className="pill pill-info" role="status">
        <CloudUpload aria-hidden="true" size={14} />
        Sincronizando…
      </span>
    )
  }
  if (pendientes > 0) {
    return (
      <span className="pill pill-warning" role="status">
        <Clock aria-hidden="true" size={14} />
        {pendientes} pendiente{pendientes !== 1 ? 's' : ''}
      </span>
    )
  }
  return (
    <span className="pill pill-success" role="status">
      <CheckCircle2 aria-hidden="true" size={14} />
      Al día
    </span>
  )
}
