import { TarjetaAlertas } from '../components/panel/TarjetaAlertas'
import { TarjetaMasVendidos } from '../components/panel/TarjetaMasVendidos'
import { TarjetaPrediccion } from '../components/panel/TarjetaPrediccion'
import { TarjetaResumenVentas } from '../components/panel/TarjetaResumenVentas'
import { TarjetaSugerencias } from '../components/panel/TarjetaSugerencias'
import { TarjetaUltimasVentas } from '../components/panel/TarjetaUltimasVentas'
import { CAPACIDADES } from '../api/capacidades'
import { useCan } from '../auth/useCan'

export function Panel() {
  const puedeReportes = useCan(CAPACIDADES.reportesVer)
  const puedeSugerencias = useCan(CAPACIDADES.sugerenciasVer)
  const puedeAlertas = useCan(CAPACIDADES.alertasVer)
  const puedePredicciones = useCan(CAPACIDADES.prediccionVer)

  return (
    <div className="pagina">
      <div className="page-header">
        <div>
          <h1>Panel</h1>
          <p className="page-subtitle">Resumen de ventas, alertas y sugerencias de compra.</p>
        </div>
      </div>
      <div className="panel-grid">
        <TarjetaResumenVentas retraso={0} />
        {puedeAlertas && <TarjetaAlertas enlace="/alertas" retraso={0.06} />}
        {puedeReportes && <TarjetaMasVendidos enlace="/reportes" retraso={0.12} />}
        <TarjetaUltimasVentas enlace="/ventas" retraso={0.18} />
        {puedeSugerencias && <TarjetaSugerencias enlace="/sugerencias" retraso={0.24} />}
        {puedePredicciones && <TarjetaPrediccion retraso={0.3} />}
      </div>
    </div>
  )
}
