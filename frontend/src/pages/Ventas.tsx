import { Link } from 'react-router'
import { ChevronLeft, ChevronRight, CircleAlert, PackagePlus, Plus } from 'lucide-react'
import { useVentas } from '../hooks/useVentas'
import { formatFecha, formatQ } from '../lib/format'
import { PillEstadoVenta } from '../components/ventas/EstadoVenta'
import { etiquetaMetodo } from '../lib/venta'

export function Ventas() {
  const { ventas, cargando, error, pagina, hayMas, irAnterior, irSiguiente, recargar } = useVentas()

  return (
    <div className="pagina">
      <div className="page-header">
        <div className="page-heading">
          <h1>Ventas</h1>
          <p className="page-sub">Historial de ventas registradas, con su folio y estado.</p>
        </div>
        <div className="page-actions">
          <Link to="/ventas/nueva" className="btn btn-primary">
            <span className="btn-icono" aria-hidden="true"><Plus /></span> Nueva venta
          </Link>
        </div>
      </div>

      <div className="card">
        {cargando && (
          <div>
            {[0, 1, 2, 3, 4].map((indice) => (
              <div key={indice} className="skeleton skeleton-row" />
            ))}
          </div>
        )}

        {!cargando && error !== null && (
          <div className="empty">
            <span className="empty-icon empty-icon-lucide" aria-hidden="true"><CircleAlert /></span>
            <h3>No se pudieron cargar las ventas</h3>
            <p>{error}</p>
            <button type="button" className="btn btn-ghost" onClick={() => void recargar()}>
              Reintentar
            </button>
          </div>
        )}

        {!cargando && error === null && ventas.length === 0 && (
          <div className="empty tabla-vacia">
            <span className="empty-icon empty-icon-lucide" aria-hidden="true"><PackagePlus /></span>
            <h3>No hay ventas que mostrar</h3>
            <p>
              {pagina > 0
                ? 'No hay ventas en esta página.'
                : 'Cuando registres ventas aparecerán aquí.'}
            </p>
          </div>
        )}

        {!cargando && error === null && ventas.length > 0 && (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Folio</th>
                  <th scope="col">Fecha</th>
                  <th scope="col">Método de pago</th>
                  <th scope="col">Estado</th>
                  <th scope="col">Total</th>
                  <th scope="col" style={{ textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {ventas.map((venta) => (
                  <tr key={venta.id}>
                    <td data-label="Folio" className="cell-strong">{venta.folio}</td>
                    <td data-label="Fecha" className="cell-muted">{formatFecha(venta.fecha)}</td>
                    <td data-label="Método de pago" className="cell-muted">
                      {etiquetaMetodo(venta.metodo_pago)}
                    </td>
                    <td data-label="Estado">
                      <PillEstadoVenta estado={venta.estado} />
                    </td>
                    <td data-label="Total" className="num">{formatQ(venta.total)}</td>
                    <td data-label="Acciones">
                      <div className="row-actions">
                        <Link to={`/ventas/${venta.id}`} className="btn btn-ghost btn-sm">
                          Ver
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="paginacion">
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={pagina === 0 || cargando}
          onClick={irAnterior}
        >
          <span className="btn-icono" aria-hidden="true"><ChevronLeft /></span> Anterior
        </button>
        <span className="paginacion-indice">Página {pagina + 1}</span>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={!hayMas || cargando}
          onClick={irSiguiente}
        >
          Siguiente <span className="btn-icono" aria-hidden="true"><ChevronRight /></span>
        </button>
      </div>
    </div>
  )
}
