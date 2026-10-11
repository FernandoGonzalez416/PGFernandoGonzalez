import { useState } from 'react'
import { CAPACIDADES } from '../api/capacidades'
import { RequireCapacidad } from '../auth/RequireCapacidad'
import { EstadoConsulta } from '../components/panel/EstadoConsulta'
import { useSugerencias, type FiltroEstado } from '../hooks/useSugerencias'
import { useCan } from '../auth/useCan'
import { actualizarSugerencia, generarSugerencias } from '../services/sugerencias'
import { useToast } from '../components/ui/ToastProvider'
import { formatCantidad, formatFecha, nombreMetodoLegible } from '../lib/format'
import type { SugerenciaRead } from '../api/types'
import { mensajeDeError } from '../lib/errores'

function PillConfianza({ nivel }: { nivel: string | null | undefined }) {
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
    <span className={clases[nivel ?? ''] ?? 'pill'}>
      {etiquetas[nivel ?? ''] ?? nivel ?? '—'}
    </span>
  )
}

export function Sugerencias() {
  const { sugerencias, total, cargando, error, filtro, setFiltro, recargar, irAnterior, irSiguiente, hayMas, pagina } = useSugerencias(20)
  const puedeGenerar = useCan(CAPACIDADES.prediccionVer)
  const puedeAtender = useCan(CAPACIDADES.sugerenciasAtender)
  const { exito, error: mostrarError } = useToast()
  const [generando, setGenerando] = useState(false)
  const [procesando, setProcesando] = useState<string | null>(null)

  const handleGenerar = async () => {
    if (!puedeGenerar) return
    setGenerando(true)
    try {
      const resultado = await generarSugerencias()
      exito(
        `Sugerencias generadas: ${resultado.sugerencias_creadas} (predicciones: ${resultado.predicciones_creadas})`,
      )
      void recargar()
    } catch (e) {
      mostrarError(mensajeDeError(e))
    } finally {
      setGenerando(false)
    }
  }

  const handleAccion = async (sugerencia: SugerenciaRead, estado: 'atendida' | 'descartada') => {
    if (!puedeAtender) return
    setProcesando(sugerencia.id)
    try {
      await actualizarSugerencia(sugerencia.id, { estado })
      exito(estado === 'atendida' ? 'Sugerencia atendida' : 'Sugerencia descartada')
      void recargar()
    } catch (e) {
      const msg = mensajeDeError(e)
      mostrarError(msg)
    } finally {
      setProcesando(null)
    }
  }

  const renderTabla = () => (
    <table className="data-table" aria-label="Sugerencias">
      <thead>
        <tr>
          <th>Producto</th>
          <th>Código</th>
          <th>Método</th>
          <th>Confianza</th>
          <th>Cantidad sugerida</th>
          <th>Prioridad</th>
          <th>Demanda / Stock</th>
          <th>Fecha</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        {sugerencias.map((s) => (
          <tr key={s.id}>
            <td data-label="Producto">{s.nombre ?? '—'}</td>
            <td data-label="Código">{s.codigo ?? '—'}</td>
            <td data-label="Método">{s.metodo ? nombreMetodoLegible(s.metodo) : '—'}</td>
            <td data-label="Confianza"><PillConfianza nivel={s.nivel_confianza} /></td>
            <td data-label="Cantidad sugerida">{formatCantidad(s.cantidad_sugerida)}</td>
            <td data-label="Prioridad">
              <span className={`pill pill-prioridad-${s.prioridad}`}>{s.prioridad}</span>
            </td>
            <td data-label="Demanda / Stock">
              {formatCantidad(s.demanda_pronosticada)} / {formatCantidad(s.stock_proyectado)}
            </td>
            <td data-label="Fecha">{formatFecha(s.fecha)}</td>
            <td data-label="Acciones" className="row-actions">
              {puedeAtender && s.estado === 'pendiente' ? (
                <>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => handleAccion(s, 'atendida')}
                    disabled={procesando === s.id}
                  >
                    Atender
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => handleAccion(s, 'descartada')}
                    disabled={procesando === s.id}
                  >
                    Descartar
                  </button>
                </>
              ) : (
                <span className="muted">{s.estado}</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )

  const botonGenerar = puedeGenerar ? (
    <button
      type="button"
      className="btn btn-primary"
      onClick={handleGenerar}
      disabled={generando}
    >
      {generando ? 'Generando...' : 'Generar sugerencias'}
    </button>
  ) : null

  return (
    <RequireCapacidad capacidad={CAPACIDADES.sugerenciasVer}>
      <div className="pagina">
        <div className="page-header">
          <div>
            <h1>Sugerencias de compra</h1>
            <p className="page-subtitle">
              Generación: <strong>modelo seleccionado por validación temporal (Random Forest, Gradient Boosting, Ridge vs. promedio móvil); confianza según evidencia P13</strong>.
            </p>
          </div>
          <div className="page-header-acciones">
            {botonGenerar}
          </div>
        </div>
        <section className="card">
          <div className="card-pad card-filtros">
            <div className="filtro-grupo">
              <label htmlFor="estado">Estado</label>
              <select
                id="estado"
                className="input"
                value={filtro}
                onChange={(e) => setFiltro(e.target.value as FiltroEstado)}
              >
                <option value="pendiente">Pendientes</option>
                <option value="atendida">Atendidas</option>
                <option value="descartada">Descartadas</option>
                <option value="todas">Todas</option>
              </select>
            </div>
            <p className="panel-metrica-contexto">Total: {formatCantidad(total)}</p>
          </div>
          <div className="table-wrap">
            <EstadoConsulta
              cargando={cargando}
              error={error}
              onReintentar={recargar}
              vacio={sugerencias.length === 0}
              mensajeVacio="No hay sugerencias para este filtro."
              hijos={renderTabla()}
            />
          </div>
          <div className="paginacion">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={irAnterior}
              disabled={pagina === 0}
            >
              Anterior
            </button>
            <span>Página {pagina + 1}</span>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={irSiguiente}
              disabled={!hayMas}
            >
              Siguiente
            </button>
          </div>
        </section>
      </div>
    </RequireCapacidad>
  )
}