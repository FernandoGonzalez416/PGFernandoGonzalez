import type { ReactNode } from 'react'
import { CircleAlert, RotateCcw } from 'lucide-react'
import { Button } from '../ui/Button'
import { EmptyState } from '../ui/EmptyState'

export function EstadoConsulta({
  cargando,
  error,
  onReintentar,
  vacio,
  mensajeVacio,
  hijos,
}: {
  cargando: boolean
  error: string | null
  onReintentar: () => void
  vacio: boolean
  mensajeVacio: string
  hijos: ReactNode
}) {
  if (cargando) {
    return (
      <div>
        {[0, 1, 2].map((indice) => (
          <div key={indice} className="skeleton skeleton-row" />
        ))}
      </div>
    )
  }

  if (error !== null) {
    return (
      <EmptyState
        icono={<CircleAlert />}
        titulo="No se pudo cargar"
        descripcion={error}
        accion={
          <Button
            variante="ghost"
            tamano="sm"
            iconoIzquierdo={<RotateCcw aria-hidden="true" />}
            onClick={onReintentar}
          >
            Reintentar
          </Button>
        }
      />
    )
  }

  if (vacio) {
    return <p className="bloque-vacio">{mensajeVacio}</p>
  }

  return <>{hijos}</>
}
