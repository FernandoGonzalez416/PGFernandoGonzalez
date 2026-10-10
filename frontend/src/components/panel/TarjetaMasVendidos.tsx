import { useMasVendidos } from '../../hooks/useMasVendidos'
import { formatCantidad, formatQ } from '../../lib/format'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'

export function TarjetaMasVendidos({ enlace }: { enlace?: string }) {
  const { items, cargando, error, recargar } = useMasVendidos(5, 7)
  const maximo = Math.max(0, ...items.map((item) => item.cantidad_vendida))

  return (
    <TarjetaPanel titulo="Más vendidos de la semana" enlace={enlace ?? '/reportes'}>
      <EstadoConsulta
        cargando={cargando}
        error={error}
        onReintentar={recargar}
        vacio={items.length === 0}
        mensajeVacio="No hay ventas registradas en la última semana."
      >
        <ol className="panel-ranking">
          {items.map((item) => {
            const ancho = maximo > 0 ? (item.cantidad_vendida / maximo) * 100 : 0
            return (
              <li key={item.producto_id} className="panel-ranking-fila">
                <div className="panel-ranking-cabecera">
                  <span className="texto-cortado">{item.nombre}</span>
                  <strong>{formatCantidad(item.cantidad_vendida)}</strong>
                </div>
                <div className="panel-ranking-bar">
                  <div className="panel-ranking-bar-rr" style={{ width: `${ancho}%` }} />
                </div>
                <span className="panel-ranking-total">{formatQ(item.total_vendido)}</span>
              </li>
            )
          })}
        </ol>
      </EstadoConsulta>
    </TarjetaPanel>
  )
}