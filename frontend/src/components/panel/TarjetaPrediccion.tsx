import { ArrowRight } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { usePredicciones } from '../../hooks/usePredicciones'
import { Link } from 'react-router'
import { nombreMetodoLegible } from '../../lib/format'

export function TarjetaPrediccion({ retraso = 0 }: { retraso?: number }) {
  const { predicciones, cargando } = usePredicciones()
  const reducirMovimiento = useReducedMotion()

  if (cargando) {
    return (
      <article className="card card-prediccion">
        <header className="card-header">
          <h3>Predicción de demanda</h3>
        </header>
        <div className="card-body">
          <div className="skeleton skeleton-row" />
          <div className="skeleton skeleton-row" />
        </div>
      </article>
    )
  }

  const conModelo = predicciones.filter((p) => p.metodo !== 'promedio_movil' && p.metodo !== 'sin_historial').length
  const conLineaBase = predicciones.filter((p) => p.metodo === 'promedio_movil').length
  const mejoras = predicciones
    .filter((p) => p.mejora_pct !== null)
    .map((p) => p.mejora_pct!)
  const mejoraMedia = mejoras.length > 0
    ? mejoras.reduce((a, b) => a + b, 0) / mejoras.length
    : 0

  const metodoMasUsado = predicciones.length > 0
    ? Object.entries(
        predicciones.reduce((acc, p) => {
          const m = nombreMetodoLegible(p.metodo)
          acc[m] = (acc[m] ?? 0) + 1
          return acc
        }, {} as Record<string, number>)
      ).sort((a, b) => b[1] - a[1])[0]?.[0]
    : '—'

  return (
    <motion.article
      className="card card-prediccion"
      initial={reducirMovimiento === true ? false : { opacity: 0, transform: 'translateY(14px)' }}
      animate={{ opacity: 1, transform: 'translateY(0px)' }}
      transition={{ duration: 0.45, delay: retraso, ease: [0.23, 1, 0.32, 1] }}
    >
      <header className="card-header">
        <h3>Predicción de demanda</h3>
      </header>
      <div className="card-body">
        <div className="prediccion-grid">
          <div className="prediccion-stat">
            <span className="stat-valor">{conModelo}</span>
            <span className="stat-etiq">Con modelo ML</span>
          </div>
          <div className="prediccion-stat">
            <span className="stat-valor">{conLineaBase}</span>
            <span className="stat-etiq">En línea base</span>
          </div>
          <div className="prediccion-stat">
            <span className={`stat-valor ${mejoraMedia >= 0 ? 'positivo' : ''}`}>
              {mejoraMedia >= 0 ? '+' : ''}{mejoraMedia.toFixed(1)}%
            </span>
            <span className="stat-etiq">Mejora media</span>
          </div>
          <div className="prediccion-stat">
            <span className="stat-valor metodo">{metodoMasUsado}</span>
            <span className="stat-etiq">Método más usado</span>
          </div>
        </div>
        <Link to="/predicciones" className="card-enlace card-enlace-icono">
          Ver todas las predicciones <ArrowRight aria-hidden="true" />
        </Link>
      </div>
    </motion.article>
  )
}