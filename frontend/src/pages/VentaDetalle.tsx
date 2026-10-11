import { useState } from 'react'
import { ArrowLeft, Ban, CircleAlert, ReceiptText, RotateCcw, X } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { CAPACIDADES } from '../api/capacidades'
import { useAuth } from '../auth/useAuth'
import { useCan } from '../auth/useCan'
import { Dialogo } from '../components/ui/Dialogo'
import { Button } from '../components/ui/Button'
import { useToast } from '../components/ui/useToast'
import { PillEstadoVenta } from '../components/ventas/EstadoVenta'
import { etiquetaMetodo } from '../lib/venta'
import { useVenta } from '../hooks/useVenta'
import { mensajeDeError } from '../lib/errores'
import { formatFecha, formatQ } from '../lib/format'
import { anularVenta } from '../services/ventas'

export function VentaDetalle() {
  const { id } = useParams<{ id: string }>()
  const { venta, cargando, error, recargar } = useVenta(id)
  const { perfil } = useAuth()
  const puedeAnularPorRol = useCan(CAPACIDADES.ventasAnular)
  const { notificar } = useToast()

  const [dialogoAbierto, setDialogoAbierto] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [procesando, setProcesando] = useState(false)

  const esPropia = venta !== null && perfil !== null && venta.usuario_id === perfil.id
  const esPadre = perfil?.rol === 'padre'
  const puedeAnular =
    puedeAnularPorRol &&
    venta !== null &&
    venta.estado === 'registrada' &&
    (!esPadre || esPropia)

  const confirmarAnulacion = async () => {
    if (venta === null || procesando) return
    const texto = motivo.trim()
    if (texto === '') {
      notificar('Escribe el motivo de la anulación.', 'error')
      return
    }
    setProcesando(true)
    try {
      await anularVenta(venta.id, { motivo_anulacion: texto })
      notificar('Venta anulada.', 'ok')
      setDialogoAbierto(false)
      setMotivo('')
      recargar()
    } catch (fallo) {
      notificar(mensajeDeError(fallo), 'error')
    } finally {
      setProcesando(false)
    }
  }

  return (
    <div className="pagina">
      <div className="page-header">
        <div className="page-heading">
          <div className="page-back">
            <Link to="/ventas" className="btn btn-ghost btn-sm"><span className="btn-icono" aria-hidden="true"><ArrowLeft /></span> Volver</Link>
          </div>
          <h1>{venta !== null ? `Venta ${venta.folio}` : 'Detalle de venta'}</h1>
          {venta !== null && (
            <p className="page-sub">
              {formatFecha(venta.fecha)} · {etiquetaMetodo(venta.metodo_pago)} ·{' '}
              <PillEstadoVenta estado={venta.estado} />
            </p>
          )}
        </div>
        {venta !== null && (
          <div className="page-actions">
            <Link to={`/ventas/${venta.id}/recibo`} className="btn btn-ghost">
              <span className="btn-icono" aria-hidden="true"><ReceiptText /></span> Ver recibo
            </Link>
            {puedeAnular && (
              <Button variante="danger" iconoIzquierdo={<Ban aria-hidden="true" />} onClick={() => setDialogoAbierto(true)}>
                Anular venta
              </Button>
            )}
          </div>
        )}
      </div>

      {cargando && (
        <div className="card">
          {[0, 1, 2, 3].map((indice) => (
            <div key={indice} className="skeleton skeleton-row" />
          ))}
        </div>
      )}

      {!cargando && error !== null && (
        <div className="card">
          <div className="empty">
            <span className="empty-icon empty-icon-lucide" aria-hidden="true"><CircleAlert /></span>
            <h3>No se pudo cargar la venta</h3>
            <p>{error}</p>
            <Button
              variante="ghost"
              iconoIzquierdo={<RotateCcw aria-hidden="true" />}
              onClick={() => void recargar()}
            >
              Reintentar
            </Button>
          </div>
        </div>
      )}

      {!cargando && error === null && venta !== null && (
        <>
          {venta.estado === 'anulada' && venta.motivo_anulacion !== null && (
            <div className="aviso aviso-red">
              <strong>Venta anulada.</strong>
              <span>Motivo: {venta.motivo_anulacion}</span>
            </div>
          )}

          <div className="card">
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th scope="col">Producto</th>
                    <th scope="col">Precio unitario</th>
                    <th scope="col">Cantidad</th>
                    <th scope="col">Subtotal</th>
                  </tr>
                </thead>
                <tbody>
                  {venta.lineas.map((linea) => (
                    <tr key={linea.producto_id}>
                      <td data-label="Producto" className="cell-strong">{linea.producto_nombre}</td>
                      <td data-label="Precio unitario" className="num">
                        {formatQ(linea.precio_unitario)}
                      </td>
                      <td data-label="Cantidad" className="num">{linea.cantidad}</td>
                      <td data-label="Subtotal" className="num">{formatQ(linea.subtotal)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="carrito-totales">
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
          </div>
        </>
      )}

      <Dialogo
        abierto={dialogoAbierto}
        titulo="Anular venta"
        onCerrar={() => {
          if (!procesando) setDialogoAbierto(false)
        }}
        pie={
          <>
            <Button
              variante="ghost"
              iconoIzquierdo={<X aria-hidden="true" />}
              disabled={procesando}
              onClick={() => setDialogoAbierto(false)}
            >
              Cancelar
            </Button>
            <Button
              variante="danger"
              iconoIzquierdo={<Ban aria-hidden="true" />}
              cargando={procesando}
              onClick={() => void confirmarAnulacion()}
            >
              Anular venta
            </Button>
          </>
        }
      >
        <div className="field">
          <label className="field-label" htmlFor="motivo-anulacion">Motivo de la anulación</label>
          <textarea
            id="motivo-anulacion"
            className="input textarea"
            rows={3}
            value={motivo}
            onChange={(evento) => setMotivo(evento.target.value)}
            placeholder="Explica por qué se anula esta venta."
          />
        </div>
      </Dialogo>
    </div>
  )
}
