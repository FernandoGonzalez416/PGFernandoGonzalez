import { useState } from 'react'
import { motion } from 'motion/react'
import { RefreshCw, TriangleAlert, X } from 'lucide-react'
import { CAPACIDADES } from '../api/capacidades'
import { RequireCapacidad } from '../auth/RequireCapacidad'
import { EstadoConsulta } from '../components/panel/EstadoConsulta'
import { usePredicciones, useSeriePrediccion } from '../hooks/usePredicciones'
import { generarSugerencias } from '../services/sugerencias'
import { useToast } from '../components/ui/ToastProvider'
import { Button } from '../components/ui/Button'
import { formatCantidad, formatFecha, nombreMetodoLegible } from '../lib/format'
import type { PrediccionRead, SerieResponse } from '../api/types'
import { mensajeDeError } from '../lib/errores'

function PillConfianza({ nivel }: { nivel: string }) {
  const clases: Record<string, string> = {
    simulacion: 'pill pill-confianza-simulacion',
    baja: 'pill pill-confianza-baja',
    alta: 'pill pill-confianza-alta',
  }
  const etiquetas: Record<string, string> = {
    simulacion: 'Simulación',
    baja: 'Baja',
    alta: 'Alta',
  }
  return (
    <span className={clases[nivel] ?? 'pill'}>
      {etiquetas[nivel] ?? nivel}
    </span>
  )
}

function MejoraPct({ mejora }: { mejora: number | null }) {
  if (mejora === null) return <span className="muted">—</span>
  if (mejora === 0) return <span className="muted">{mejora.toFixed(1)}%</span>
  const positivo = mejora > 0
  return (
    <span className={positivo ? 'mejora-positiva' : 'mejora-negativa'}>
      {positivo ? '+' : ''}{mejora.toFixed(1)}%
    </span>
  )
}

interface HistorialItem {
  fecha: string
  unidades: number
}

interface PronosticoItem {
  fecha: string
  unidades: number
}

export function Predicciones() {
  const { predicciones, cargando, error, recargar } = usePredicciones()
  const [productoSeleccionado, setProductoSeleccionado] = useState<PrediccionRead | null>(null)
  const { serie, cargando: cargandoSerie, error: errorSerie } = useSeriePrediccion(
    productoSeleccionado?.producto_id ?? null,
  )
  const { exito, error: mostrarError } = useToast()
  const [actualizando, setActualizando] = useState(false)

  const handleActualizar = async () => {
    setActualizando(true)
    try {
      const resultado = await generarSugerencias()
      exito(
        `Predicciones actualizadas: ${resultado.predicciones_creadas} productos. ` +
        Object.entries(resultado.por_metodo ?? {})
          .map(([m, c]) => `${nombreMetodoLegible(m)}: ${c}`)
          .join(', '),
      )
      void recargar()
      setProductoSeleccionado(null)
    } catch (e) {
      mostrarError(mensajeDeError(e))
    } finally {
      setActualizando(false)
    }
  }

  const conModelo = predicciones.filter((p) => p.metodo !== 'promedio_movil' && p.metodo !== 'sin_historial').length
  const conLineaBase = predicciones.filter((p) => p.metodo === 'promedio_movil').length
  const mejoras = predicciones
    .filter((p) => p.mejora_pct !== null)
    .map((p) => p.mejora_pct!)
  const mejoraMedia = mejoras.length > 0
    ? mejoras.reduce((a, b) => a + b, 0) / mejoras.length
    : 0

  return (
    <RequireCapacidad capacidad={CAPACIDADES.prediccionVer}>
      <div className="pagina">
        <div className="page-header">
          <div>
            <h1>Predicción de demanda</h1>
            <p className="page-subtitle">
              Pronóstico a 7 días por producto. Modelo seleccionado por validación temporal contra línea base (promedio móvil 7 días).
            </p>
          </div>
          <div className="page-header-acciones">
            <Button
              variante="primary"
              iconoIzquierdo={<RefreshCw aria-hidden="true" />}
              cargando={actualizando}
              onClick={handleActualizar}
            >
              Actualizar predicciones
            </Button>
          </div>
        </div>

        <div className="aviso-simulacion" role="alert">
          <span className="aviso-icon-lucide" aria-hidden="true"><TriangleAlert /></span>
          <p><strong>Datos de simulación:</strong> la precisión mostrada valida el funcionamiento del modelo,
          no su desempeño real en el negocio. Con historial real el modelo se recalibra (P13).</p>
        </div>

        <div className="resumen-prediccion grid-3">
          <article className="card card-metrica">
            <div className="metrica-valor">{conModelo}</div>
            <div className="metrica-etiq">Productos con modelo ML</div>
          </article>
          <article className="card card-metrica">
            <div className="metrica-valor">{conLineaBase}</div>
            <div className="metrica-etiq">Productos en línea base</div>
          </article>
          <article className="card card-metrica">
            <div className={`metrica-valor ${mejoraMedia >= 0 ? 'positivo' : ''}`}>
              {mejoraMedia >= 0 ? '+' : ''}{mejoraMedia.toFixed(1)}%
            </div>
            <div className="metrica-etiq">Mejora media vs. línea base</div>
          </article>
        </div>

        <section className="card" aria-labelledby="tabla-predicciones-label">
          <h2 id="tabla-predicciones-label" className="card-title">Predicciones por producto</h2>
          <div className="table-wrap">
            <EstadoConsulta
              cargando={cargando}
              error={error}
              onReintentar={recargar}
              vacio={predicciones.length === 0}
              mensajeVacio="No hay predicciones disponibles."
              hijos={
                <table className="data-table" aria-label="Predicciones de demanda por producto">
                  <thead>
                    <tr>
                      <th>Producto</th>
                      <th>Código</th>
                      <th>Método</th>
                      <th>Demanda 7 días</th>
                      <th>Error semanal medio (unidades), modelo / base</th>
                      <th>Mejora</th>
                      <th>Confianza</th>
                      <th>Obs. usadas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predicciones.map((p) => (
                      <tr
                        key={p.id}
                        onClick={() => setProductoSeleccionado(p)}
                        style={{ cursor: 'pointer' }}
                        className={productoSeleccionado?.id === p.id ? 'seleccionada' : ''}
                      >
                        <td data-label="Producto">{p.nombre}</td>
                        <td data-label="Código">{p.codigo}</td>
                        <td data-label="Método">{nombreMetodoLegible(p.metodo)}</td>
                        <td data-label="Demanda 7 días">
                          {formatCantidad(p.demanda_pronosticada)}
                          {p.intervalo_inf !== null && p.intervalo_sup !== null && (
                            <span className="intervalo">
                              [{formatCantidad(p.intervalo_inf)} – {formatCantidad(p.intervalo_sup)}]
                            </span>
                          )}
                        </td>
                        <td data-label="Error semanal medio (unidades), modelo / base">
                          {p.mae_validacion !== null ? formatCantidad(p.mae_validacion) : '—'}
                          {p.mae_linea_base !== null && p.mae_validacion !== null && (
                            <span className="muted"> / {formatCantidad(p.mae_linea_base)}</span>
                          )}
                        </td>
                        <td data-label="Mejora">
                          <MejoraPct mejora={p.mejora_pct} />
                        </td>
                        <td data-label="Confianza">
                          <PillConfianza nivel={p.nivel_confianza} />
                        </td>
                        <td data-label="Obs. usadas">{p.observaciones_usadas}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              }
            />
          </div>
        </section>

        {productoSeleccionado && (
          <motion.div
            className="detalle-prediccion"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            <DetallePrediccion
              prediccion={productoSeleccionado}
              serie={serie}
              cargandoSerie={cargandoSerie}
              errorSerie={errorSerie}
              onCerrar={() => setProductoSeleccionado(null)}
            />
          </motion.div>
        )}
      </div>
    </RequireCapacidad>
  )
}

function DetallePrediccion({
  prediccion,
  serie,
  cargandoSerie,
  errorSerie,
  onCerrar,
}: {
  prediccion: PrediccionRead
  serie: SerieResponse | null
  cargandoSerie: boolean
  errorSerie: string | null
  onCerrar: () => void
}) {
  const historialRaw = (serie?.historial ?? []) as { [key: string]: unknown }[]
  const pronosticoRaw = (serie?.pronostico ?? []) as { [key: string]: unknown }[]
  
  const historial: HistorialItem[] = historialRaw.map((h) => ({
    fecha: String(h.fecha),
    unidades: Number(h.unidades),
  }))
  const pronostico: PronosticoItem[] = pronosticoRaw.map((p) => ({
    fecha: String(p.fecha),
    unidades: Number(p.unidades),
  }))

  const ancho = 720
  const alto = 300
  const margen = { top: 20, right: 60, bottom: 50, left: 60 }
  const anchoUtil = ancho - margen.left - margen.right
  const altoUtil = alto - margen.top - margen.bottom

  const todosDatos = [
    ...historial.slice(-60).map((h) => ({
      fecha: h.fecha,
      unidades: h.unidades,
      tipo: 'historial' as const,
    })),
    ...pronostico.map((p) => ({
      fecha: p.fecha,
      unidades: p.unidades,
      tipo: 'pronostico' as const,
    })),
  ]

  const fechas = todosDatos.map((d) => new Date(d.fecha))
  const unidades = todosDatos.map((d) => d.unidades)
  const fechaMin = new Date(Math.min(...fechas.map((f) => f.getTime())))
  const fechaMax = new Date(Math.max(...fechas.map((f) => f.getTime())))
  const unidadMax = Math.max(...unidades, 1)

  const escalaX = (fecha: Date) =>
    margen.left + ((fecha.getTime() - fechaMin.getTime()) / (fechaMax.getTime() - fechaMin.getTime())) * anchoUtil
  const escalaY = (valor: number) =>
    margen.top + altoUtil - (valor / unidadMax) * altoUtil

  const pathHistorial = historial
    .slice(-60)
    .map((h, i) => {
      const x = escalaX(new Date(h.fecha))
      const y = escalaY(h.unidades)
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    .join(' ')

  const pathPronostico = pronostico
    .map((p, i) => {
      const x = escalaX(new Date(p.fecha))
      const y = escalaY(p.unidades)
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    .join(' ')

  return (
    <section className="card detalle-prediccion-panel" role="region" aria-labelledby="detalle-titulo">
      <header className="detalle-header">
        <h2 id="detalle-titulo">Detalle: {prediccion.nombre} ({prediccion.codigo})</h2>
        <button type="button" className="btn btn-ghost btn-sm" onClick={onCerrar}>
          <span className="btn-icono" aria-hidden="true"><X /></span> Cerrar detalle
        </button>
      </header>

      <div className="detalle-grid">
        <div className="detalle-grafico">
          <h3>Historial (60 días) y pronóstico (7 días)</h3>
          {cargandoSerie ? (
            <div className="grafico-cargando">Cargando serie...</div>
          ) : errorSerie ? (
            <div className="grafico-error">{errorSerie}</div>
          ) : (
            <figure className="grafico-svg" role="img" aria-label={`Gráfico de demanda para ${prediccion.nombre}. Línea continua: historial últimos 60 días. Línea punteada: pronóstico próximos 7 días.`}>
              <svg width={ancho} height={alto} viewBox={`0 0 ${ancho} ${alto}`}>
                {/* Ejes */}
                <line
                  x1={margen.left}
                  y1={margen.top}
                  x2={margen.left}
                  y2={alto - margen.bottom}
                  stroke="var(--line)"
                  strokeWidth={1}
                />
                <line
                  x1={margen.left}
                  y1={alto - margen.bottom}
                  x2={ancho - margen.right}
                  y2={alto - margen.bottom}
                  stroke="var(--line)"
                  strokeWidth={1}
                />

                {/* Marcas Y */}
                {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
                  const y = margen.top + altoUtil * (1 - frac)
                  const val = Math.round(unidadMax * frac)
                  return (
                    <g key={frac}>
                      <line
                        x1={margen.left - 6}
                        y1={y}
                        x2={margen.left}
                        y2={y}
                        stroke="var(--line)"
                        strokeWidth={1}
                      />
                      <text
                        x={margen.left - 10}
                        y={y + 4}
                        textAnchor="end"
                        fontSize={11}
                        fill="var(--ink-faint)"
                        fontFamily="var(--fuente-cuerpo)"
                      >
                        {val}
                      </text>
                    </g>
                  )
                })}

                {/* Marcas X - fechas */}
                {Array.from({ length: 6 }, (_, i) => {
                  const t = i / 5
                  const x = margen.left + t * anchoUtil
                  const fecha = new Date(fechaMin.getTime() + t * (fechaMax.getTime() - fechaMin.getTime()))
                  return (
                    <g key={i}>
                      <line
                        x1={x}
                        y1={alto - margen.bottom}
                        x2={x}
                        y2={alto - margen.bottom + 6}
                        stroke="var(--line)"
                        strokeWidth={1}
                      />
                      <text
                        x={x}
                        y={alto - margen.bottom + 20}
                        textAnchor="middle"
                        fontSize={10}
                        fill="var(--ink-faint)"
                        fontFamily="var(--fuente-cuerpo)"
                      >
                        {fecha.toLocaleDateString('es-GT', { month: 'short', day: 'numeric' })}
                      </text>
                    </g>
                  )
                })}

                {/* Intervalo de confianza - banda */}
                {pronostico.length > 0 && (
                  <path
                    d={`M ${margen.left} ${alto - margen.bottom} L ${pathPronostico} L ${ancho - margen.right} ${alto - margen.bottom} Z`}
                    fill="var(--primary-soft)"
                    opacity={0.3}
                  />
                )}

                {/* Historial */}
                {historial.length > 0 && (
                  <path
                    d={pathHistorial}
                    stroke="var(--terracota)"
                    strokeWidth={2.5}
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* Pronóstico */}
                {pronostico.length > 0 && (
                  <path
                    d={pathPronostico}
                    stroke="var(--terracota)"
                    strokeWidth={2.5}
                    strokeDasharray="6 4"
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* Puntos historial */}
                {historial.slice(-60).map((h, i) => (
                  <circle
                    key={i}
                    cx={escalaX(new Date(h.fecha))}
                    cy={escalaY(h.unidades)}
                    r={3}
                    fill="var(--terracota)"
                  />
                ))}

                {/* Puntos pronóstico */}
                {pronostico.map((p, i) => (
                  <circle
                    key={i}
                    cx={escalaX(new Date(p.fecha))}
                    cy={escalaY(p.unidades)}
                    r={3}
                    fill="var(--terracota)"
                    stroke="var(--surface)"
                    strokeWidth={2}
                  />
                ))}
              </svg>
              <figcaption className="grafico-leyenda">
                <span className="leyenda-item"><span className="leyenda-color historial" /> Historial (últimos 60 días)</span>
                <span className="leyenda-item"><span className="leyenda-color pronostico" /> Pronóstico (7 días)</span>
              </figcaption>
            </figure>
          )}

          {/* Tabla alternativa para accesibilidad */}
          <details className="tabla-accesible">
            <summary>Ver datos en tabla (accesible para lectores de pantalla)</summary>
            <div className="table-wrap">
              <table className="data-table" aria-label="Datos de historial y pronóstico">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Unidades</th>
                    <th>Tipo</th>
                  </tr>
                </thead>
                <tbody>
                  {historial.slice(-60).map((h) => (
                    <tr key={h.fecha}>
                      <td>{formatFecha(h.fecha)}</td>
                      <td>{formatCantidad(h.unidades)}</td>
                      <td><span className="pill pill-historial">Historial</span></td>
                    </tr>
                  ))}
                  {pronostico.map((p) => (
                    <tr key={p.fecha}>
                      <td>{formatFecha(p.fecha)}</td>
                      <td>{formatCantidad(p.unidades)}</td>
                      <td><span className="pill pill-pronostico">Pronóstico</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>

        <div className="detalle-info">
          <div className="info-grid">
            <article className="card info-card">
              <h4>Modelo elegido</h4>
              <p className="valor-grande">{nombreMetodoLegible(prediccion.metodo)}</p>
            </article>
            <article className="card info-card">
              <h4>Confianza</h4>
              <p className="valor-grande"><PillConfianza nivel={prediccion.nivel_confianza} /></p>
            </article>
            <article className="card info-card">
              <h4>Error semanal medio (unidades) del modelo</h4>
              <p className="valor-grande">{prediccion.mae_validacion !== null ? formatCantidad(prediccion.mae_validacion) : '—'}</p>
            </article>
            <article className="card info-card">
              <h4>Error semanal medio (unidades) línea base</h4>
              <p className="valor-grande">{prediccion.mae_linea_base !== null ? formatCantidad(prediccion.mae_linea_base) : '—'}</p>
            </article>
            <article className="card info-card">
              <h4>Mejora vs. base</h4>
              <p className={`valor-grande ${prediccion.mejora_pct !== null && prediccion.mejora_pct >= 0 ? 'positivo' : ''}`}>
                {prediccion.mejora_pct !== null ? (prediccion.mejora_pct >= 0 ? '+' : '') + prediccion.mejora_pct.toFixed(1) + '%' : '—'}
              </p>
            </article>
            <article className="card info-card">
              <h4>Obs. usadas</h4>
              <p className="valor-grande">{prediccion.observaciones_usadas}</p>
            </article>
          </div>

          {prediccion.metodo === 'promedio_movil' && prediccion.motivo && (
            <div className="card aviso-linea-base">
              <h4>¿Por qué se usa la línea base?</h4>
              <p>{prediccion.motivo}</p>
            </div>
          )}

          {prediccion.metodo === 'sin_historial' && (
            <div className="card aviso-linea-base">
              <h4>Sin historial de ventas</h4>
              <p>Este producto no tiene ventas registradas. No se genera pronóstico de demanda.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}