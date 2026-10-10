import { Link } from 'react-router'
import type { ReactNode } from 'react'

export function TarjetaPanel({
  titulo,
  enlace,
  etiquetaEnlace = 'Ver más',
  ancho = 'normal',
  hijos,
}: {
  titulo: string
  enlace?: string
  etiquetaEnlace?: string
  ancho?: 'normal' | 'ancho'
  hijos: ReactNode
}) {
  return (
    <section className={`card panel-tarjeta${ancho === 'ancho' ? ' panel-tarjeta-ancha' : ''}`}>
      <div className="card-head">
        <h2>{titulo}</h2>
        {enlace !== undefined && (
          <Link to={enlace} className="panel-enlace">
            {etiquetaEnlace}
          </Link>
        )}
      </div>
      <div className="card-pad">{hijos}</div>
    </section>
  )
}