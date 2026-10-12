import { useState } from 'react'
import { motion } from 'motion/react'
import { AlertTriangle, CheckCircle2, Clock, RefreshCw, Trash2 } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { formatQ } from '../lib/format'
import { useOffline } from '../offline/useOffline'
import type { VentaCola } from '../offline/types'

function EstadoBadge({ estado }: { estado: VentaCola['estado'] }) {
  if (estado === 'sincronizada') {
    return (
      <span className="pill pill-success">
        <CheckCircle2 aria-hidden="true" size={14} />
        Sincronizada
      </span>
    )
  }
  if (estado === 'requiere_revision') {
    return (
      <span className="pill pill-danger">
        <AlertTriangle aria-hidden="true" size={14} />
        Requiere revisión
      </span>
    )
  }
  return (
    <span className="pill pill-warning">
      <Clock aria-hidden="true" size={14} />
      Pendiente
    </span>
  )
}

/**
 * Ventas registradas sin conexión que aún no están confirmadas por el servidor
 * (P27/F5). Lee el estado de la cola desde `useOffline`.
 */
export function VentasPendientes() {
  const { ventas, sincronizando, authRequerida, eliminarVenta, reintentar, sincronizar } = useOffline()
  const [confirmandoDescarte, setConfirmandoDescarte] = useState<string | null>(null)

  const ventasOrdenadas = [...ventas].sort(
    (a, b) => new Date(b.fecha).getTime() - new Date(a.fecha).getTime(),
  )
  const hayPendientes = ventas.some((venta) => venta.estado === 'pendiente')

  return (
    <div className="pagina ventas-pendientes">
      <div className="page-header">
        <div className="page-heading">
          <h1>Ventas pendientes</h1>
          <p className="page-sub">
            Ventas registradas sin conexión que aún no se han sincronizado con el servidor.
          </p>
        </div>
        {hayPendientes && (
          <Button
            variante="primary"
            cargando={sincronizando}
            disabled={sincronizando}
            iconoIzquierdo={<RefreshCw aria-hidden="true" size={16} />}
            onClick={() => void sincronizar()}
          >
            Sincronizar ahora
          </Button>
        )}
      </div>

      {authRequerida && (
        <div className="card card-pad" role="alert">
          Tu sesión expiró. Vuelve a iniciar sesión para sincronizar las ventas pendientes.
        </div>
      )}

      <div className="card">
        <table className="tabla">
          <thead>
            <tr>
              <th>Folio</th>
              <th>Estado</th>
              <th>Fecha</th>
              <th>Total</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {ventasOrdenadas.length === 0 ? (
              <tr>
                <td colSpan={5}>
                  <div className="empty">
                    <span className="empty-icon empty-icon-lucide" aria-hidden="true">
                      <CheckCircle2 />
                    </span>
                    <h3>No hay ventas pendientes</h3>
                    <p>Todas las ventas han sido sincronizadas correctamente.</p>
                  </div>
                </td>
              </tr>
            ) : (
              ventasOrdenadas.map((venta) => (
                <motion.tr
                  key={venta.client_request_id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.2 }}
                >
                  <td>
                    <span className="cell-strong">{venta.folio_provisional}</span>
                    {venta.folio_definitivo && (
                      <span className="cell-muted"> → {venta.folio_definitivo}</span>
                    )}
                  </td>
                  <td>
                    <EstadoBadge estado={venta.estado} />
                    {venta.error && (
                      <span className="cell-muted" style={{ display: 'block', fontSize: '0.8rem' }}>
                        {venta.error}
                      </span>
                    )}
                  </td>
                  <td>{new Date(venta.fecha).toLocaleString('es-GT')}</td>
                  <td className="num">{formatQ(venta.total)}</td>
                  <td>
                    {venta.estado === 'requiere_revision' && (
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <Button
                          variante="ghost"
                          tamano="sm"
                          iconoIzquierdo={<RefreshCw aria-hidden="true" size={14} />}
                          onClick={() => reintentar(venta.client_request_id)}
                          disabled={sincronizando}
                        >
                          Reintentar
                        </Button>
                        {confirmandoDescarte === venta.client_request_id ? (
                          <>
                            <Button
                              variante="danger"
                              tamano="sm"
                              onClick={() => {
                                eliminarVenta(venta.client_request_id)
                                setConfirmandoDescarte(null)
                              }}
                            >
                              Confirmar
                            </Button>
                            <Button
                              variante="ghost"
                              tamano="sm"
                              onClick={() => setConfirmandoDescarte(null)}
                            >
                              Cancelar
                            </Button>
                          </>
                        ) : (
                          <Button
                            variante="ghost"
                            tamano="sm"
                            iconoIzquierdo={<Trash2 aria-hidden="true" size={14} />}
                            onClick={() => setConfirmandoDescarte(venta.client_request_id)}
                          >
                            Descartar
                          </Button>
                        )}
                      </div>
                    )}
                  </td>
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
