import { formatCantidad, formatFecha } from '../../lib/format'

export type FilaMovimiento = {
  id: string
  fecha: string
  producto: string
  tipo: string
  referenciaTipo: string
  cantidad: string
  nota: string | null
}

const CLASE_TIPO = new Map<string, string>([
  ['entrada', 'pill-good'],
  ['salida', 'pill-red'],
  ['ajuste', 'pill-amber'],
])

const ETIQUETA_REFERENCIA = new Map<string, string>([
  ['venta', 'Venta'],
  ['compra', 'Compra'],
  ['ajuste', 'Ajuste'],
  ['vencimiento', 'Vencimiento'],
  ['devolucion', 'Devolución'],
  ['inicial', 'Inicial'],
])

export function TablaMovimientos({ filas }: { filas: FilaMovimiento[] }) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">Fecha</th>
            <th scope="col">Producto</th>
            <th scope="col">Tipo</th>
            <th scope="col">Origen</th>
            <th scope="col">Cantidad</th>
            <th scope="col">Nota</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => (
            <tr key={fila.id}>
              <td data-label="Fecha" className="cell-muted">{formatFecha(fila.fecha)}</td>
              <td data-label="Producto" className="cell-strong">{fila.producto}</td>
              <td data-label="Tipo">
                <span className={`pill ${CLASE_TIPO.get(fila.tipo) ?? 'pill-neutral'}`}>
                  {fila.tipo}
                </span>
              </td>
              <td data-label="Origen" className="cell-muted">
                {ETIQUETA_REFERENCIA.get(fila.referenciaTipo) ?? fila.referenciaTipo}
              </td>
              <td data-label="Cantidad" className="num">{formatCantidad(fila.cantidad)}</td>
              <td data-label="Nota" className="cell-muted">{fila.nota ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
