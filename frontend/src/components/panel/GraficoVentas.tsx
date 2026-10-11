import { useMemo } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import type { ResumenVentaDia } from '../../api/types'
import { formatFechaCorta } from '../../lib/fecha'
import { formatCantidad, formatQ, parseDecimal } from '../../lib/format'

function resumenAccesible(dias: ResumenVentaDia[]): string {
  const partes = dias.map((dia) => {
    const quetzales = formatQ(dia.total_vendido)
    if (dia.num_ventas === 0) return `${formatFechaCorta(dia.fecha)}: sin ventas`
    return `${formatFechaCorta(dia.fecha)}: ${dia.num_ventas} venta(s), ${quetzales}`
  })
  return `Ventas por día. ${partes.join('. ')}.`
}

/**
 * Gráfica de barras de la semana: barras HTML animadas (crecen desde abajo,
 * stagger por día, valor encima —nunca dentro— y día máximo destacado).
 * Solo anima transform/opacity; respeta prefers-reduced-motion.
 */
export function GraficoVentas({ dias }: { dias: ResumenVentaDia[] }) {
  const reducirMovimiento = useReducedMotion()
  const maximo = useMemo(() => {
    const m = Math.max(0, ...dias.map((dia) => parseDecimal(dia.total_vendido) ?? 0))
    return m <= 0 ? 1 : m
  }, [dias])

  const indiceMaximo = useMemo(() => {
    let mejor = -1
    let mejorValor = -1
    dias.forEach((dia, indice) => {
      const valor = parseDecimal(dia.total_vendido) ?? 0
      if (valor > mejorValor) {
        mejorValor = valor
        mejor = indice
      }
    })
    return mejorValor > 0 ? mejor : -1
  }, [dias])

  return (
    <figure className="grafico-ventas">
      <div className="grafico-max-linea" aria-hidden="true">
        <span className="num">{formatQ(String(maximo))}</span>
      </div>
      <div
        className="grafico-barras"
        role="img"
        aria-label={resumenAccesible(dias)}
      >
        <div className="grafico-lineas" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        {dias.map((dia, indice) => {
          const valor = parseDecimal(dia.total_vendido) ?? 0
          const proporcion = maximo > 0 ? valor / maximo : 0
          const alturaPct = valor <= 0 ? 0 : Math.max(8, proporcion * 100)
          const esMaximo = indice === indiceMaximo
          const etiqueta = `${formatFechaCorta(dia.fecha)}: ${dia.num_ventas} venta(s), ${formatQ(dia.total_vendido)}`
          return (
            <div key={dia.fecha} className="grafico-columna" title={etiqueta}>
              <span className={`grafico-valor num${esMaximo ? ' grafico-valor-max' : ''}`}>
                {valor > 0 ? formatQ(dia.total_vendido) : '—'}
              </span>
              <div className="grafico-pista">
                {valor <= 0 ? (
                  <div className="grafico-barra-vacia" aria-hidden="true">
                    <span />
                  </div>
                ) : (
                  <motion.div
                    className={`grafico-barra-html${esMaximo ? ' grafico-barra-max' : ''}`}
                    style={{ height: `${alturaPct}%` }}
                    initial={reducirMovimiento === true ? false : { transform: 'scaleY(0)' }}
                    animate={{ transform: 'scaleY(1)' }}
                    transition={{
                      duration: 0.55,
                      delay: reducirMovimiento === true ? 0 : indice * 0.06,
                      ease: [0.32, 0.72, 0, 1],
                    }}
                  />
                )}
              </div>
              <span className="grafico-dia">{formatFechaCorta(dia.fecha)}</span>
              {esMaximo && <span className="grafico-insignia">Mayor</span>}
            </div>
          )
        })}
      </div>
      <figcaption className="grafico-leyenda">
        {formatCantidad(dias.length)} días · {formatQ(maximo)} es la mayor venta del día
      </figcaption>
    </figure>
  )
}
