import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router'
import { listarNotificaciones, marcarNotificacionLeida } from '../../services/notificaciones'
import type { NotificacionItem } from '../../api/types'
import { formatFechaCorta } from '../../lib/fecha'

export function CampanaNotificaciones() {
  const [abierto, setAbierto] = useState(false)
  const [notificaciones, setNotificaciones] = useState<NotificacionItem[]>([])
  const [cargando, setCargando] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    function alClicExterno(evento: MouseEvent) {
      if (ref.current !== null && !ref.current.contains(evento.target as Node)) {
        setAbierto(false)
      }
    }
    document.addEventListener('mousedown', alClicExterno)
    return () => document.removeEventListener('mousedown', alClicExterno)
  }, [])

  useEffect(() => {
    let cancelado = false
    ;(async () => {
      try {
        const datos = await listarNotificaciones({ leida: false, limite: 8 })
        if (!cancelado) setNotificaciones(datos.items)
      } finally {
        if (!cancelado) setCargando(false)
      }
    })()
    return () => {
      cancelado = true
    }
  }, [])

  const contar = notificaciones.length
  const marcar = async (id: string) => {
    try {
      await marcarNotificacionLeida(id)
      await cargar()
    } catch {
      // ignorar
    }
  }

  const verTodas = () => {
    setAbierto(false)
    navigate('/notificaciones')
  }

  return (
    <div className="campana-wrap" ref={ref}>
      <button
        type="button"
        className="campana-btn"
        aria-haspopup="true"
        aria-expanded={abierto}
        onClick={() => {
          setAbierto((v) => !v)
          if (!abierto) void cargar()
        }}
      >
        <span aria-hidden="true">🔔</span>
        {contar > 0 && <span className="campana-badge">{contar}</span>}
      </button>
      {abierto && (
        <div className="campana-panel">
          <div className="campana-head">
            <strong>Notificaciones</strong>
            {contar > 0 && (
              <button type="button" className="link" onClick={verTodas}>
                Ver todas
              </button>
            )}
          </div>
          <div className="campana-lista">
            {cargando && <p className="muted">Cargando...</p>}
            {!cargando && contar === 0 && <p className="muted">No tienes notificaciones nuevas.</p>}
            {!cargando &&
              notificaciones.map((n) => (
                <button
                  type="button"
                  key={n.id}
                  className="campana-item"
                  onClick={() => marcar(n.id)}
                >
                  <div className="campana-item-info">
                    <strong>{n.tipo.replace('_', ' ')}</strong>
                    <p>{n.mensaje}</p>
                    <span className="notif-fecha">{formatFechaCorta(n.fecha)}</span>
                  </div>
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}