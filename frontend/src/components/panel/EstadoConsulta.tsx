import type { ReactNode } from 'react'

export function EstadoConsulta({
  cargando,
  error,
  onReintentar,
  vacio,
  mensajeVacio,
  hijos,
}: {
  cargando: boolean
  error: string | null
  onReintentar: () => void
  vacio: boolean
  mensajeVacio: string
  hijos: ReactNode
}) {
  if (cargando) {
    return (
      <div>
        {[0, 1, 2].map((indice) => (
          <div key={indice} className="skeleton skeleton-row" />
        ))}
      </div>
    )
  }

  if (error !== null) {
    return (
      <div className="empty bloque-error">
        <span className="empty-icon" aria-hidden="true">!</span>
        <p>{error}</p>
        <button type="button" className="btn btn-ghost btn-sm" onClick={onReintentar}>
          Reintentar
        </button>
      </div>
    )
  }

  if (vacio) {
    return <p className="bloque-vacio">{mensajeVacio}</p>
  }

  return <>{hijos}</>
}