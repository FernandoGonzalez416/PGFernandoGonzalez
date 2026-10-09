import type { LineaCarrito, TotalesCarrito } from '../../lib/carrito'
import { formatQ } from '../../lib/format'

export function TablaCarrito({
  lineas,
  totales,
  onCambiarCantidad,
  onQuitar,
}: {
  lineas: LineaCarrito[]
  totales: TotalesCarrito
  onCambiarCantidad: (productoId: string, cantidad: number) => void
  onQuitar: (productoId: string) => void
}) {
  return (
    <>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Producto</th>
              <th scope="col">Precio</th>
              <th scope="col">Cantidad</th>
              <th scope="col">Importe</th>
              <th scope="col" style={{ textAlign: 'right' }}>Quitar</th>
            </tr>
          </thead>
          <tbody>
            {lineas.map((linea) => (
              <tr key={linea.productoId}>
                <td data-label="Producto">
                  <div className="cell-strong">{linea.nombre}</div>
                  <div className="cell-muted">{linea.codigo}</div>
                </td>
                <td data-label="Precio" className="num">
                  {formatQ(linea.precioUnitarioCents / 100)}
                </td>
                <td data-label="Cantidad">
                  <div className="cantidad-control">
                    <button
                      type="button"
                      className="icon-btn"
                      aria-label={`Quitar una unidad de ${linea.nombre}`}
                      onClick={() => onCambiarCantidad(linea.productoId, linea.cantidad - 1)}
                    >
                      −
                    </button>
                    <input
                      className="input cantidad-input"
                      inputMode="numeric"
                      aria-label={`Cantidad de ${linea.nombre}`}
                      value={linea.cantidad}
                      onChange={(evento) =>
                        onCambiarCantidad(linea.productoId, Number(evento.target.value))
                      }
                    />
                    <button
                      type="button"
                      className="icon-btn"
                      aria-label={`Agregar una unidad de ${linea.nombre}`}
                      disabled={linea.cantidad >= linea.existenciaDisponible}
                      onClick={() => onCambiarCantidad(linea.productoId, linea.cantidad + 1)}
                    >
                      ＋
                    </button>
                  </div>
                </td>
                <td data-label="Importe" className="num">
                  {formatQ((linea.precioUnitarioCents * linea.cantidad) / 100)}
                </td>
                <td data-label="Quitar">
                  <div className="row-actions">
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={() => onQuitar(linea.productoId)}
                    >
                      Quitar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="carrito-totales">
        <div className="totales-fila">
          <span>Subtotal</span>
          <span className="num">{formatQ(totales.subtotalCents / 100)}</span>
        </div>
        <div className="totales-fila">
          <span>Descuento</span>
          <span className="num">− {formatQ(totales.descuentoCents / 100)}</span>
        </div>
        <div className="totales-fila total">
          <span>Total</span>
          <span className="num">{formatQ(totales.totalCents / 100)}</span>
        </div>
      </div>
    </>
  )
}
