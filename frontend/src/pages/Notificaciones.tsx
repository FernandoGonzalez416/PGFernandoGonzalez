import { useState } from 'react'
import { CheckCheck, Eye, RotateCcw } from 'lucide-react'
import { CAPACIDADES } from '../api/capacidades'
import { RequireCapacidad } from '../auth/RequireCapacidad'
import { useNotificaciones } from '../hooks/useNotificaciones'
import { listarNotificaciones, marcarNotificacionLeida } from '../services/notificaciones'
import { formatFecha } from '../lib/format'
import { mensajeDeError } from '../lib/errores'
import { useToast } from '../components/ui/ToastProvider'
import { Button } from '../components/ui/Button'
import { Link } from 'react-router'

export function Notificaciones() {
  const [filtro, setFiltro] = useState<boolean | undefined>(undefined)
  const { notificaciones, total, cargando, error, recargar } = useNotificaciones({
    leida: filtro,
    limite: 50,
  })
  const { exito, error: mostrarError } = useToast()
  const [procesando, setProcesando] = useState<string | null>(null)

  const marcarComoLeida = async (id: string) => {
    setProcesando(id)
    try {
      await marcarNotificacionLeida(id)
      exito('Notificación marcada como leída')
      void recargar()
    } catch (e) {
      mostrarError(mensajeDeError(e))
    } finally {
      setProcesando(null)
    }
  }

  const marcarTodas = async () => {
    try {
      const sinLeer = await listarNotificaciones({ leida: false, limite: 100 })
      await Promise.all(sinLeer.items.map((n) => marcarNotificacionLeida(n.id)))
      exito('Todas las notificaciones se marcaron como leídas')
      void recargar()
    } catch (e) {
      mostrarError(mensajeDeError(e))
    }
  }

  return (
    <RequireCapacidad capacidad={CAPACIDADES.alertasVer}>
      <div className="pagina">
        <div className="page-header">
          <div>
            <h1>Notificaciones</h1>
            <p className="page-subtitle">Historial de alertas y sugerencias.</p>
          </div>
          <div className="page-header-acciones">
            <Button variante="ghost" iconoIzquierdo={<CheckCheck aria-hidden="true" />} onClick={marcarTodas}>
              Marcar todas como leídas
            </Button>
            <Button variante="ghost" iconoIzquierdo={<RotateCcw aria-hidden="true" />} onClick={recargar}>
              Actualizar
            </Button>
          </div>
        </div>
        <section className="card">
          <div className="card-pad card-filtros">
            <div className="filtro-grupo">
              <label htmlFor="filtro">Filtrar</label>
              <select
                id="filtro"
                className="input"
                value={filtro === undefined ? 'todas' : filtro ? 'leidas' : 'sinleer'}
                onChange={(e) => {
                  const v = e.target.value
                  setFiltro(v === 'todas' ? undefined : v === 'leidas')
                }}
              >
                <option value="todas">Todas</option>
                <option value="sinleer">Sin leer</option>
                <option value="leidas">Leídas</option>
              </select>
            </div>
            <p className="panel-metrica-contexto">Total: {total}</p>
          </div>
          <div className="table-wrap">
            {cargando && <div className="skeleton skeleton-row" />}
            {error !== null && <p className="bloque-error">{error}</p>}
            {cargando === false && error === null && notificaciones.length === 0 && (
              <p className="bloque-vacio">No hay notificaciones para este filtro.</p>
            )}
            <ul className="lista-notificaciones">
              {notificaciones.map((n) => (
                <li key={n.id} className={`notif-item${n.leida ? ' notif-leida' : ''}`}>
                  <div className="notif-info">
                    <strong>{n.tipo.replace('_', ' ')}</strong>
                    <p>{n.mensaje}</p>
                    <span className="notif-fecha">{formatFecha(n.fecha)}</span>
                  </div>
                  <div className="notif-acciones">
                    {!n.leida && (
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => marcarComoLeida(n.id)}
                        disabled={procesando === n.id}
                      >
                        <span className="btn-icono" aria-hidden="true"><Eye /></span> Marcar como leída
                      </button>
                    )}
                    {n.tipo === 'sugerencia_compra' && (
                      <Link to="/sugerencias" className="btn btn-ghost btn-sm">
                        Ver sugerencias
                      </Link>
                    )}
                    {n.tipo === 'bajo_stock' || n.tipo === 'vencimiento_proximo' ? (
                      <Link to="/alertas" className="btn btn-ghost btn-sm">
                        Ver alertas
                      </Link>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>
    </RequireCapacidad>
  )
}