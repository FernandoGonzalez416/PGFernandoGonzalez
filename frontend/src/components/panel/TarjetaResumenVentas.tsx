import { useResumenVentas } from '../../hooks/useResumenVentas'
import { formatCantidad, formatFecha, formatQ } from '../../lib/format'
import { GraficoVentas } from './GraficoVentas'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'

export function TarjetaResumenVentas() {
  const { resumen, cargando, error, recargar } = useResumenVentas()

  return (
    <TarjetaPanel titulo="Ventas de la semana" enlace="/ventas" ancho="ancho">
      <EstadoConsulta
        cargando={cargando}
        error={error}
        onReintentar={recargar}
        vacio={resumen !== null && resumen.por_dia.length === 0}
        mensajeVacio="Todavía no hay ventas en este periodo."
      >
        {resumen !== null && (
          <>
            <div className="panel-metricas">
              <div className="panel-metrica">
                <span className="panel-metrica-etiqueta">Total vendido</span>
                <span className="panel-metrica-valor">{formatQ(resumen.total_vendido)}</span>
              </div>
              <div className="panel-metrica">
                <span className="panel-metrica-etiqueta">Ventas</span>
                <span className="panel-metrica-valor">
                  {formatCantidad(resumen.num_ventas)}
                </span>
              </div>
              <div className="panel-metrica">
                <span className="panel-metrica-etiqueta">Periodo</span>
                <span className="panel-metrica-contexto">
                  {formatFecha(resumen.fecha_inicio)} — {formatFecha(resumen.fecha_fin)}
                </span>
              </div>
            </div>
            <GraficoVentas dias={resumen.por_dia} />
          </>
        )}
      </EstadoConsulta>
    </TarjetaPanel>
  )
}