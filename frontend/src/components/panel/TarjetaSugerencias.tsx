import { motion, useReducedMotion } from 'motion/react'
import { useSugerencias } from '../../hooks/useSugerencias'
import { formatCantidad } from '../../lib/format'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'

export function TarjetaSugerencias({ enlace, retraso = 0 }: { enlace?: string; retraso?: number }) {
  const { sugerencias, total, cargando, error, recargar } = useSugerencias(5)
  const reducirMovimiento = useReducedMotion()

  const contenido = (
    <>
      <p className="panel-metrica-contexto panel-en-linea num">
        {total} pendiente(s) por revisar
      </p>
      <ul className="panel-lista">
        {sugerencias.map((sugerencia, indice) => (
          <motion.li
            key={sugerencia.id}
            className="panel-fila"
            initial={reducirMovimiento === true ? false : { opacity: 0, transform: 'translateX(-8px)' }}
            animate={{ opacity: 1, transform: 'translateX(0px)' }}
            transition={{ duration: 0.32, delay: indice * 0.05, ease: [0.23, 1, 0.32, 1] }}
          >
            <span className="texto-cortado">{sugerencia.nombre ?? sugerencia.codigo}</span>
            <span className={`pill pill-prioridad-${sugerencia.prioridad}`}>
              {formatCantidad(sugerencia.cantidad_sugerida)} · {sugerencia.prioridad}
            </span>
          </motion.li>
        ))}
      </ul>
    </>
  )

  return (
    <TarjetaPanel
      titulo="Sugerencias de compra"
      enlace={enlace ?? '/sugerencias'}
      retraso={retraso}
      hijos={
        <EstadoConsulta
          cargando={cargando}
          error={error}
          onReintentar={recargar}
          vacio={sugerencias.length === 0}
          mensajeVacio="No hay sugerencias pendientes."
          hijos={contenido}
        />
      }
    />
  )
}
