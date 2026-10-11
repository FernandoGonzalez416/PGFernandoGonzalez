import { Component, type ReactNode } from 'react'
import { CircleAlert, RotateCcw } from 'lucide-react'
import { Button } from './ui/Button'
import { EmptyState } from './ui/EmptyState'

type Props = { children: ReactNode }
type State = { error: Error | null }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('ErrorBoundary', error, info)
  }

  render() {
    const { error } = this.state
    if (error !== null) {
      return (
        <div className="pagina">
          <EmptyState
            icono={<CircleAlert />}
            titulo="Algo salió mal"
            descripcion="La aplicación tuvo un error inesperado. Recarga la página e inténtalo de nuevo."
            accion={
              <Button
                variante="primary"
                iconoIzquierdo={<RotateCcw aria-hidden="true" />}
                onClick={() => {
                  window.location.reload()
                }}
              >
                Recargar
              </Button>
            }
          />
        </div>
      )
    }
    return this.props.children
  }
}