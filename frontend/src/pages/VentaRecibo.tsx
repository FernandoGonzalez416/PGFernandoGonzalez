import { Link, useParams } from 'react-router'
import { PillEstadoVenta } from '../components/ventas/EstadoVenta'
import { etiquetaMetodo } from '../lib/venta'
import { useVenta } from '../hooks/useVenta'
import { APP_NAME, DATOS_FICTICIOS } from '../lib/env'
import { formatFecha, formatQ } from '../lib/format'

export function VentaRecibo() {
  const { id } = useParams<{ id: string }>()
  const { venta, cargando, error, recargar } = useVenta(id)

  return (
    <div className="pagina recibo-pagina">
      <div className="recibo-acciones no-print">
        <Link to={id !== undefined ? `/ventas/${id}` : '/ventas'} className="btn btn-ghost btn-sm">
          ← Volver
        </Link>
        <button
          type="button"
          className="btn btn-primary"
          disabled={venta === null}
          onClick={() => window.print()}
        >
          Imprimir
        </button>
      </div>

      {cargando && (
        <div className="card recibo">
          {[0, 1, 2, 3].map((indice) => (
            <div key={indice} className="skeleton skeleton-row" />
          ))}
        </div>
      )}

      {!cargando && error !== null && (
        <div className="card">
          <div className="empty">
            <span className="empty-icon" aria-hidden="true">!</span>
            <h3>No se pudo cargar el recibo</h3>
            <p>{error}</p>
            <button type="button" className="btn btn-ghost" onClick={() => void recargar()}>
              Reintentar
            </button>
          </div>
        </div>
      )}

      {!cargando && error === null && venta !== null && (
        <div className="card recibo">
          {venta.estado === 'anulada' && <div className="recibo-anulada">ANULADA</div>}

          {DATOS_FICTICIOS && <div className="recibo-demo">Datos de prueba (simulación)</div>}

          <div className="recibo-encabezado">
            <h1>{APP_NAME}</h1>
            <p>Recibo de venta</p>
          </div>

          <div className="recibo-meta">
            <div>Folio: <strong>{venta.folio}</strong></div>
            <div>{formatFecha(venta.fecha)}</div>
            <div>Pago: {etiquetaMetodo(venta.metodo_pago)}</div>
            <div>Estado: <PillEstadoVenta estado={venta.estado} /></div>
          </div>

          <table className="recibo-lineas">
            <thead>
              <tr>
                <th scope="col">Cant.</th>
                <th scope="col">Producto</th>
                <th scope="col">P. unit.</th>
                <th scope="col">Importe</th>
              </tr>
            </thead>
            <tbody>
              {venta.lineas.map((linea) => (
                <tr key={linea.producto_id}>
                  <td className="num">{linea.cantidad}</td>
                  <td>{linea.producto_nombre}</td>
                  <td className="num">{formatQ(linea.precio_unitario)}</td>
                  <td className="num">{formatQ(linea.subtotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="recibo-totales">
            <div className="totales-fila">
              <span>Subtotal</span>
              <span className="num">{formatQ(venta.subtotal)}</span>
            </div>
            <div className="totales-fila">
              <span>Descuento</span>
              <span className="num">− {formatQ(venta.descuento)}</span>
            </div>
            <div className="totales-fila total">
              <span>Total</span>
              <span className="num">{formatQ(venta.total)}</span>
            </div>
          </div>

          {venta.estado === 'anulada' && venta.motivo_anulacion !== null && (
            <p className="recibo-motivo">Motivo de anulación: {venta.motivo_anulacion}</p>
          )}

          <p className="recibo-leyenda">
            Recibo interno — no es factura ni documento tributario (no SAT/FEL).
          </p>
        </div>
      )}
    </div>
  )
}
