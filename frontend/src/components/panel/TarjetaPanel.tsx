import { Link } from 'react-router'
import { motion, useReducedMotion } from 'motion/react'
import type { ReactNode } from 'react'

export function TarjetaPanel({
  titulo,
  enlace,
  etiquetaEnlace = 'Ver más',
  ancho = 'normal',
  retraso = 0,
  hijos,
}: {
  titulo: string
  enlace?: string
  etiquetaEnlace?: string
  ancho?: 'normal' | 'ancho'
  retraso?: number
  hijos: ReactNode
}) {
  const reducirMovimiento = useReducedMotion()
  return (
    <motion.section
      className={`card panel-tarjeta${ancho === 'ancho' ? ' panel-tarjeta-ancha' : ''}`}
      initial={reducirMovimiento === true ? false : { opacity: 0, transform: 'translateY(14px)' }}
      animate={{ opacity: 1, transform: 'translateY(0px)' }}
      transition={{ duration: 0.45, delay: retraso, ease: [0.23, 1, 0.32, 1] }}
    >
      <div className="card-head">
        <h2>{titulo}</h2>
        {enlace !== undefined && (
          <Link to={enlace} className="panel-enlace">
            {etiquetaEnlace}
          </Link>
        )}
      </div>
      <div className="card-pad">{hijos}</div>
    </motion.section>
  )
}
