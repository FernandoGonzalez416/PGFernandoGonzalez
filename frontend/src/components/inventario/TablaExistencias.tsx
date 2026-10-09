import { formatCantidad } from '../../lib/format'

export type FilaExistencia = {
  productoId: string
  nombre: string
  codigo: string
  unidad: string
  cantidad: string
  umbral: string | null
  almacen: string
}

function estadoDeFila(fila: FilaExistencia): { etiqueta: string; clase: string } {
  const cantidad = Number(fila.cantidad)
  const umbral = fila.umbral !== null ? Number(fila.umbral) : null
  if (cantidad <= 0) return { etiqueta: 'Agotado', clase: 'pill-red' }
  if (umbral !== null && cantidad <= umbral) return { etiqueta: 'Bajo', clase: 'pill-amber' }
  return { etiqueta: 'Disponible', clase: 'pill-good' }
}

export function TablaExistencias({
  filas,
  puedeAjustar,
  onAjustar,
}: {
  filas: FilaExistencia[]
  puedeAjustar: boolean
  onAjustar: (fila: FilaExistencia) => void
}) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">Producto</th>
            <th scope="col">Almacén</th>
            <th scope="col">Existencia</th>
            <th scope="col">Umbral mínimo</th>
            <th scope="col">Estado</th>
            {puedeAjustar && (
              <th scope="col" style={{ textAlign: 'right' }}>Ajuste</th>
            )}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => {
            const estado = estadoDeFila(fila)
            return (
              <tr key={fila.productoId}>
                <td data-label="Producto">
                  <div className="cell-strong">{fila.nombre}</div>
                  <div className="cell-muted">{fila.codigo}</div>
                </td>
                <td data-label="Almacén" className="cell-muted">{fila.almacen}</td>
                <td data-label="Existencia" className="num">
                  {formatCantidad(fila.cantidad)} {fila.unidad}
                </td>
                <td data-label="Umbral mínimo" className="num">
                  {fila.umbral !== null ? formatCantidad(fila.umbral) : '—'}
                </td>
                <td data-label="Estado">
                  <span className={`pill ${estado.clase}`}>{estado.etiqueta}</span>
                </td>
                {puedeAjustar && (
                  <td data-label="Ajuste">
                    <div className="row-actions">
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => onAjustar(fila)}
                      >
                        Ajustar
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
