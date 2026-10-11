import { motion } from 'motion/react'
import type { ReactNode } from 'react'

/** Estado vacío/error con icono Lucide en medallón nude (reemplaza los símbolos "!" / "＋" / emojis). */
export function EmptyState({
  icono,
  titulo,
  descripcion,
  accion,
}: {
  icono: ReactNode
  titulo: string
  descripcion?: string
  accion?: ReactNode
}) {
  return (
    <motion.div
      className="empty"
      initial={{ opacity: 0, transform: 'translateY(6px)' }}
      animate={{ opacity: 1, transform: 'translateY(0px)' }}
      transition={{ duration: 0.26, ease: [0.23, 1, 0.32, 1] }}
    >
      <span className="empty-icon empty-icon-lucide" aria-hidden="true">
        {icono}
      </span>
      <h3>{titulo}</h3>
      {descripcion !== undefined && <p>{descripcion}</p>}
      {accion !== undefined && <div className="empty-accion">{accion}</div>}
    </motion.div>
  )
}
