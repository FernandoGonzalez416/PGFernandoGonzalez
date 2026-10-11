import { motion, useReducedMotion } from 'motion/react'
import { useVentas } from '../../hooks/useVentas'
import { formatQ } from '../../lib/format'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'

const ETIQUETAS_ESTADO: Record<string, string | null> = {
  activa: null,
  anulada: 'Anulada',
}

export function TarjetaUltimasVentas({ enlace, retraso = 0 }: { enlace?: string; retraso?: number }) {
  const { ventas, cargando, error, recargar } = useVentas(5)
  const reducirMovimiento = useReducedMotion()

  const contenido = (
    <ul className="panel-lista">
      {ventas.map((venta, indice) => {
        const etiqueta = ETIQUETAS_ESTADO[venta.estado]
        return (
          <motion.li
            key={venta.id}
            className="panel-fila"
            initial={reducirMovimiento === true ? false : { opacity: 0, transform: 'translateX(-8px)' }}
            animate={{ opacity: 1, transform: 'translateX(0px)' }}
            transition={{ duration: 0.32, delay: indice * 0.05, ease: [0.23, 1, 0.32, 1] }}
          >
            <span className="texto-cortado">{venta.folio}</span>
            <span className="panel-fila-valor">
              {etiqueta === null ? (
                <strong className="panel-monto num">{formatQ(venta.total)}</strong>
              ) : (
                <span className="pill pill-anulada">{etiqueta}</span>
              )}
            </span>
          </motion.li>
        )
      })}
    </ul>
  )

  return (
    <TarjetaPanel
      titulo="Últimas ventas"
      enlace={enlace ?? '/ventas'}
      retraso={retraso}
      hijos={
        <EstadoConsulta
          cargando={cargando}
          error={error}
          onReintentar={recargar}
          vacio={ventas.length === 0}
          mensajeVacio="Todavía no hay ventas registradas."
          hijos={contenido}
        />
      }
    />
  )
}
