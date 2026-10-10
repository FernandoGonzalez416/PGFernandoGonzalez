import { useMemo } from 'react'
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

export function GraficoVentas({ dias }: { dias: ResumenVentaDia[] }) {
  const maximo = useMemo(() => {
    const m = Math.max(0, ...dias.map((dia) => parseDecimal(dia.total_vendido) ?? 0))
    return m <= 0 ? 1 : m
  }, [dias])

  const anchoBarra = useMemo(() => {
    const disponibles = 320 - dias.length * 6
    return Math.min(34, Math.max(10, Math.floor(disponibles / dias.length)))
  }, [dias])

  const alto = 92

  return (
    <figure className="grafico-ventas">
      <svg
        role="img"
        aria-label={resumenAccesible(dias)}
        viewBox={`0 0 320 ${alto + 22}`}
        width="100%"
        height="auto"
        className="grafico-ventas-svg"
      >
        <g className="grafico-eje">
          <line x1="0" y1={alto} x2="320" y2={alto} />
          <text x="0" y={alto - 4}>
            {formatQ(String(maximo))}
          </text>
        </g>
        {dias.map((dia, indice) => {
          const valor = parseDecimal(dia.total_vendido) ?? 0
          const altura = Math.max(valor > 0 ? 2 : 0, (valor / maximo) * (alto - 4))
          const x = indice * (anchoBarra + 6)
          return (
            <g key={dia.fecha}>
              <rect
                x={x}
                y={alto - altura}
                width={anchoBarra}
                height={altura}
                rx="3"
                className={valor <= 0 ? 'grafico-barra grafico-barra-vacia' : 'grafico-barra'}
              >
                <title>{`${formatFechaCorta(dia.fecha)}: ${dia.num_ventas} venta(s), ${formatQ(
                  dia.total_vendido,
                )}`}</title>
              </rect>
              <text x={x + anchoBarra / 2} y={alto + 15} className="grafico-etiqueta">
                {formatFechaCorta(dia.fecha)}
              </text>
            </g>
          )
        })}
      </svg>
      <figcaption className="grafico-leyenda">
        {formatCantidad(dias.length)} días · {formatQ(maximo)} es la mayor venta del día
      </figcaption>
    </figure>
  )
}