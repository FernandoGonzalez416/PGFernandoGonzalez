import { useVentas } from '../../hooks/useVentas'
import { formatQ } from '../../lib/format'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'
import type { VentaRead } from '../../api/types'

const ETIQUETAS_ESTADO: Record<string, string | null> = {
  activa: null,
  anulada: 'Anulada',
}

export function TarjetaUltimasVentas({ enlace }: { enlace?: string }) {
  const { ventas, cargando, error, recargar } = useVentas(5)

  return (
    <TarjetaPanel titulo="Últimas ventas" enlace={enlace ?? '/ventas'}>
      <EstadoConsulta
        cargando={cargando}
        error={error}
        onReintentar={recargar}
        vacio={ventas.length === 0}
        mensajeVacio="Todavía no hay ventas registradas."
      >
        <ul className="panel-lista">
          {ventas.map((venta: VentaRead) => {
            const etiqueta = ETIQUETAS_ESTADO[venta.estado]
            return (
              <li key={venta.id} className="panel-fila">
                <span className="texto-cortado">{venta.folio}</span>
                <span className="panel-fila-valor">
                  {etiqueta === null ? (
                    <strong className="panel-monto">{formatQ(venta.total)}</strong>
                  ) : (
                    <span className="pill pill-anulada">{etiqueta}</span>
                  )}
                </span>
              </li>
            )
          })}
        </ul>
      </EstadoConsulta>
    </TarjetaPanel>
  )
}