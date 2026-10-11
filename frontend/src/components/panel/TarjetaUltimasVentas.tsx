import { useVentas } from '../../hooks/useVentas'
import { formatQ } from '../../lib/format'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'

const ETIQUETAS_ESTADO: Record<string, string | null> = {
  activa: null,
  anulada: 'Anulada',
}

export function TarjetaUltimasVentas({ enlace }: { enlace?: string }) {
  const { ventas, cargando, error, recargar } = useVentas(5)

  const contenido = (
    <ul className="panel-lista">
      {ventas.map((venta) => {
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
  )

  return (
    <TarjetaPanel
      titulo="Últimas ventas"
      enlace={enlace ?? '/ventas'}
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