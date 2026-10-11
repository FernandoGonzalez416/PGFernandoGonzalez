import { useMasVendidos } from '../../hooks/useMasVendidos'
import { formatCantidad, formatQ } from '../../lib/format'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'

export function TarjetaMasVendidos({ enlace }: { enlace?: string }) {
  const { items, cargando, error, recargar } = useMasVendidos(5, 7)
  const maximo = Math.max(0, ...items.map((item) => Number(item.cantidad_vendida)))

  const contenido = (
    <ol className="panel-ranking">
      {items.map((item) => {
        const cantidad = Number(item.cantidad_vendida)
        const ancho = maximo > 0 ? (cantidad / maximo) * 100 : 0
        return (
          <li key={item.producto_id} className="panel-ranking-fila">
            <div className="panel-ranking-cabecera">
              <span className="texto-cortado">{item.nombre}</span>
              <strong>{formatCantidad(cantidad)}</strong>
            </div>
            <div className="panel-ranking-bar">
              <div className="panel-ranking-bar-rr" style={{ width: `${ancho}%` }} />
            </div>
            <span className="panel-ranking-total">{formatQ(item.total_vendido)}</span>
          </li>
        )
      })}
    </ol>
  )

  return (
    <TarjetaPanel
      titulo="Más vendidos de la semana"
      enlace={enlace ?? '/reportes'}
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