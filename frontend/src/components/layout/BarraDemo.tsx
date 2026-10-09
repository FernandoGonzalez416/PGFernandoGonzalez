import { DATOS_FICTICIOS } from '../../lib/env'

export function BarraDemo() {
  if (!DATOS_FICTICIOS) return null
  return (
    <div className="demo-banner" role="note">
      <span aria-hidden="true">●</span>
      <span>
        <strong>Datos de prueba:</strong> la información mostrada es ficticia y sirve para validar
        el sistema.
      </span>
    </div>
  )
}
