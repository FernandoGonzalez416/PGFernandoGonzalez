import { motion } from 'motion/react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variante = 'primary' | 'ghost' | 'nude' | 'danger'
type Tamano = 'sm' | 'md'

interface Props
  extends Omit<
    ButtonHTMLAttributes<HTMLButtonElement>,
    'onDrag' | 'onDragStart' | 'onDragEnd' | 'onAnimationStart' | 'onAnimationEnd'
  > {
  variante?: Variante
  tamano?: Tamano
  bloque?: boolean
  cargando?: boolean
  iconoIzquierdo?: ReactNode
  iconoDerecho?: ReactNode
}

const CLASES: Record<Variante, string> = {
  primary: 'btn btn-primary',
  ghost: 'btn btn-ghost',
  nude: 'btn btn-nude',
  danger: 'btn btn-danger',
}

/** Botón del sistema de diseño Familia de la Cruz: física real (tap 0.97), hover con elevación, iconos Lucide. */
export function Button({
  variante = 'primary',
  tamano = 'md',
  bloque = false,
  cargando = false,
  iconoIzquierdo,
  iconoDerecho,
  disabled,
  children,
  className,
  ...resto
}: Props) {
  const clases = [
    CLASES[variante],
    tamano === 'sm' ? 'btn-sm' : '',
    bloque ? 'btn-block' : '',
    className ?? '',
  ]
    .filter((c) => c !== '')
    .join(' ')

  return (
    <motion.button
      type={resto.type ?? 'button'}
      className={clases}
      disabled={disabled === true || cargando}
      whileTap={{ scale: 0.97 }}
      transition={{ duration: 0.13, ease: [0.23, 1, 0.32, 1] }}
      {...resto}
    >
      {cargando ? (
        <span className="btn-spinner" aria-hidden="true" />
      ) : (
        iconoIzquierdo !== undefined && (
          <span className="btn-icono" aria-hidden="true">
            {iconoIzquierdo}
          </span>
        )
      )}
      <span className="btn-texto">{cargando ? 'Cargando…' : children}</span>
      {!cargando && iconoDerecho !== undefined && (
        <span className="btn-icono" aria-hidden="true">
          {iconoDerecho}
        </span>
      )}
    </motion.button>
  )
}
