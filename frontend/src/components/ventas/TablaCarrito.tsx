import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { Minus, Plus, Trash2 } from 'lucide-react'
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
  const reducirMovimiento = useReducedMotion()

  const restar = (linea: LineaCarrito) => {
    if (linea.cantidad <= 1) {
      onQuitar(linea.productoId)
      return
    }
    onCambiarCantidad(linea.productoId, linea.cantidad - 1)
  }

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
            <AnimatePresence initial={false}>
              {lineas.map((linea) => (
                <motion.tr
                  key={linea.productoId}
                  initial={reducirMovimiento === true ? false : { opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
                >
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
                        aria-label={
                          linea.cantidad <= 1
                            ? `Quitar ${linea.nombre} del carrito`
                            : `Quitar una unidad de ${linea.nombre}`
                        }
                        title={linea.cantidad <= 1 ? 'Quitar del carrito' : 'Quitar una unidad'}
                        onClick={() => restar(linea)}
                      >
                        <Minus aria-hidden="true" />
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
                        title="Agregar una unidad"
                        disabled={linea.cantidad >= linea.existenciaDisponible}
                        onClick={() => onCambiarCantidad(linea.productoId, linea.cantidad + 1)}
                      >
                        <Plus aria-hidden="true" />
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
                        title={`Quitar ${linea.nombre} del carrito`}
                        onClick={() => onQuitar(linea.productoId)}
                      >
                        <span className="btn-icono" aria-hidden="true">
                          <Trash2 />
                        </span>
                        Quitar
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </AnimatePresence>
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
