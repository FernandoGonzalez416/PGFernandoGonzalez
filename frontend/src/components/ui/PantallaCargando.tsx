export function PantallaCargando({ mensaje = 'Cargando…' }: { mensaje?: string }) {
  return (
    <div className="pantalla-cargando" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <p>{mensaje}</p>
    </div>
  )
}
