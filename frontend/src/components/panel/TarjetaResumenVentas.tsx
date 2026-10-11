import { motion, useReducedMotion } from 'motion/react'
import { useResumenVentas } from '../../hooks/useResumenVentas'
import { formatCantidad, formatFecha, formatQ } from '../../lib/format'
import { GraficoVentas } from './GraficoVentas'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'

export function TarjetaResumenVentas({ retraso = 0 }: { retraso?: number }) {
  const { resumen, cargando, error, recargar } = useResumenVentas()
  const reducirMovimiento = useReducedMotion()

  const contenido = resumen !== null ? (
    <>
      <div className="panel-metricas">
        {[
          { etiqueta: 'Total vendido', valor: formatQ(resumen.total_vendido), destacado: true },
          { etiqueta: 'Ventas', valor: formatCantidad(resumen.num_ventas), destacado: false },
        ].map((metrica, indice) => (
          <motion.div
            key={metrica.etiqueta}
            className="panel-metrica"
            initial={reducirMovimiento === true ? false : { opacity: 0, transform: 'translateY(8px)' }}
            animate={{ opacity: 1, transform: 'translateY(0px)' }}
            transition={{
              duration: 0.35,
              delay: indice * 0.07,
              ease: [0.23, 1, 0.32, 1],
            }}
          >
            <span className="panel-metrica-etiqueta">{metrica.etiqueta}</span>
            <span className={`panel-metrica-valor num${metrica.destacado ? ' panel-metrica-valor-total' : ''}`}>
              {metrica.valor}
            </span>
          </motion.div>
        ))}
        <motion.div
          className="panel-metrica"
          initial={reducirMovimiento === true ? false : { opacity: 0, transform: 'translateY(8px)' }}
          animate={{ opacity: 1, transform: 'translateY(0px)' }}
          transition={{ duration: 0.35, delay: 0.14, ease: [0.23, 1, 0.32, 1] }}
        >
          <span className="panel-metrica-etiqueta">Periodo</span>
          <span className="panel-metrica-contexto num">
            {formatFecha(resumen.fecha_inicio)} — {formatFecha(resumen.fecha_fin)}
          </span>
        </motion.div>
      </div>
      <GraficoVentas dias={resumen.por_dia} />
    </>
  ) : null

  return (
    <TarjetaPanel
      titulo="Ventas de la semana"
      enlace="/ventas"
      ancho="ancho"
      retraso={retraso}
      hijos={
        <EstadoConsulta
          cargando={cargando}
          error={error}
          onReintentar={recargar}
          vacio={resumen !== null && resumen.por_dia.length === 0}
          mensajeVacio="Todavía no hay ventas en este periodo."
          hijos={contenido}
        />
      }
    />
  )
}
