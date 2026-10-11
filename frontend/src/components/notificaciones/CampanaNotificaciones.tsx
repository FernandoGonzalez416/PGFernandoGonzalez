import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { useNavigate } from 'react-router'
import { Bell } from 'lucide-react'
import { listarNotificaciones, marcarNotificacionLeida } from '../../services/notificaciones'
import type { NotificacionItem } from '../../api/types'
import { formatFechaCorta } from '../../lib/fecha'

export function CampanaNotificaciones() {
  const [abierto, setAbierto] = useState(false)
  const [notificaciones, setNotificaciones] = useState<NotificacionItem[]>([])
  const [cargando, setCargando] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  const cargar = async () => {
    try {
      setCargando(true)
      const datos = await listarNotificaciones({ leida: false, limite: 8 })
      setNotificaciones(datos.items)
    } finally {
      setCargando(false)
    }
  }

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
        await cargar()
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
      <motion.button
        type="button"
        className="campana-btn"
        aria-label="Notificaciones"
        aria-haspopup="true"
        aria-expanded={abierto}
        whileTap={{ scale: 0.93 }}
        transition={{ duration: 0.13, ease: [0.23, 1, 0.32, 1] }}
        onClick={() => {
          setAbierto((v) => !v)
          if (!abierto) void cargar()
        }}
      >
        <Bell aria-hidden="true" />
        {contar > 0 && <span className="campana-badge">{contar}</span>}
      </motion.button>
      <AnimatePresence>
        {abierto && (
          <motion.div
            className="campana-panel"
            initial={{ opacity: 0, transform: 'scale(0.96) translateY(-4px)' }}
            animate={{ opacity: 1, transform: 'scale(1) translateY(0px)' }}
            exit={{ opacity: 0, transform: 'scale(0.96) translateY(-4px)' }}
            transition={{ duration: 0.16, ease: [0.23, 1, 0.32, 1] }}
            style={{ transformOrigin: 'top right' }}
          >
            <div className="campana-head">
              <strong>Notificaciones</strong>
              {contar > 0 && (
                <button type="button" className="panel-enlace" onClick={verTodas}>
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
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
