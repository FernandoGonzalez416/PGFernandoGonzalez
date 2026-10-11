import { motion } from 'motion/react'
import type { ReactNode } from 'react'

/** Tarjeta base: superficie cálida, borde hairline teñido, sombra suave, entrada con motion. */
export function Card({
  titulo,
  subtitulo,
  acciones,
  children,
}: {
  titulo?: string
  subtitulo?: string
  acciones?: ReactNode
  children: ReactNode
}) {
  const conCabecera = titulo !== undefined || acciones !== undefined
  return (
    <motion.section
      className="card"
      initial={{ opacity: 0, transform: 'translateY(8px)' }}
      animate={{ opacity: 1, transform: 'translateY(0px)' }}
      transition={{ duration: 0.26, ease: [0.23, 1, 0.32, 1] }}
    >
      {conCabecera && (
        <header className="card-head">
          <div>
            {titulo !== undefined && <h2>{titulo}</h2>}
            {subtitulo !== undefined && <p className="detalle-meta">{subtitulo}</p>}
          </div>
          {acciones !== undefined && <div className="card-head-acciones">{acciones}</div>}
        </header>
      )}
      <div className="card-pad">{children}</div>
    </motion.section>
  )
}
