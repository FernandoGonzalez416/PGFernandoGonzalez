import { Component, type ReactNode } from 'react'

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
          <div className="empty">
            <span className="empty-icon" aria-hidden="true">!</span>
            <h2>Algo salió mal</h2>
            <p>La aplicación tuvo un error inesperado. Recarga la página e inténtalo de nuevo.</p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                window.location.reload()
              }}
            >
              Recargar
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}