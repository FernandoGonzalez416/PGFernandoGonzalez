import { motion, useReducedMotion } from 'motion/react'
import { useMasVendidos } from '../../hooks/useMasVendidos'
import { formatCantidad, formatQ } from '../../lib/format'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'

export function TarjetaMasVendidos({ enlace, retraso = 0 }: { enlace?: string; retraso?: number }) {
  const { items, cargando, error, recargar } = useMasVendidos(5, 7)
  const reducirMovimiento = useReducedMotion()
  const maximo = Math.max(0, ...items.map((item) => Number(item.cantidad_vendida)))

  const contenido = (
    <ol className="panel-ranking">
      {items.map((item, indice) => {
        const cantidad = Number(item.cantidad_vendida)
        const ancho = maximo > 0 ? (cantidad / maximo) * 100 : 0
        return (
          <motion.li
            key={item.producto_id}
            className="panel-ranking-fila"
            initial={reducirMovimiento === true ? false : { opacity: 0, transform: 'translateX(-8px)' }}
            animate={{ opacity: 1, transform: 'translateX(0px)' }}
            transition={{ duration: 0.35, delay: indice * 0.06, ease: [0.23, 1, 0.32, 1] }}
          >
            <div className="panel-ranking-cabecera">
              <span className="texto-cortado">{item.nombre}</span>
              <strong className="num">{formatCantidad(cantidad)}</strong>
            </div>
            <div className="panel-ranking-bar">
              <motion.div
                className="panel-ranking-bar-rr"
                initial={reducirMovimiento === true ? false : { transform: 'scaleX(0)' }}
                animate={{ transform: 'scaleX(1)' }}
                style={{ width: `${ancho}%` }}
                transition={{ duration: 0.5, delay: 0.1 + indice * 0.06, ease: [0.32, 0.72, 0, 1] }}
              />
            </div>
            <span className="panel-ranking-total num">{formatQ(item.total_vendido)}</span>
          </motion.li>
        )
      })}
    </ol>
  )

  return (
    <TarjetaPanel
      titulo="Más vendidos de la semana"
      enlace={enlace ?? '/reportes'}
      retraso={retraso}
      hijos={
        <EstadoConsulta
          cargando={cargando}
          error={error}
          onReintentar={recargar}
          vacio={items.length === 0}
          mensajeVacio="No hay ventas registradas en la última semana."
          hijos={contenido}
        />
      }
    />
  )
}
