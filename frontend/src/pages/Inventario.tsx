import { useMemo, useState } from 'react'
import { Check, CircleAlert, PackagePlus, RotateCcw, X } from 'lucide-react'
import { CAPACIDADES } from '../api/capacidades'
import { useCan } from '../auth/useCan'
import {
  TablaExistencias,
  type FilaExistencia,
} from '../components/inventario/TablaExistencias'
import {
  TablaMovimientos,
  type FilaMovimiento,
} from '../components/inventario/TablaMovimientos'
import { Dialogo } from '../components/ui/Dialogo'
import { Button } from '../components/ui/Button'
import { useToast } from '../components/ui/useToast'
import { useExistencias } from '../hooks/useExistencias'
import { useMovimientos } from '../hooks/useMovimientos'
import { useProductos } from '../hooks/useProductos'
import { mensajeDeError } from '../lib/errores'
import { ajustarExistencia } from '../services/inventario'

export function Inventario() {
  const { productos, cargando: cargandoProductos, error: errorProductos } = useProductos()
  const {
    existencias,
    cargando: cargandoExistencias,
    error: errorExistencias,
    recargar: recargarExistencias,
  } = useExistencias()
  const puedeVerMovimientos = useCan(CAPACIDADES.inventarioVerMovimientos)
  const {
    movimientos,
    cargando: cargandoMovimientos,
    error: errorMovimientos,
    recargar: recargarMovimientos,
  } = useMovimientos(50)
  const puedeAjustar = useCan(CAPACIDADES.inventarioAjustar)
  const { notificar } = useToast()

  const [ajuste, setAjuste] = useState<FilaExistencia | null>(null)
  const [deltaTexto, setDeltaTexto] = useState('')
  const [nota, setNota] = useState('')
  const [procesando, setProcesando] = useState(false)

  const productosPorId = useMemo(
    () => new Map(productos.map((producto) => [producto.id, producto])),
    [productos],
  )

  const filasExistencias = useMemo<FilaExistencia[]>(
    () =>
      existencias.map((existencia) => {
        const producto = productosPorId.get(existencia.producto_id)
        return {
          productoId: existencia.producto_id,
          nombre: producto?.nombre ?? 'Producto no disponible',
          codigo: producto?.codigo ?? existencia.producto_id.slice(0, 8),
          unidad: producto?.unidad_medida ?? '',
          cantidad: existencia.cantidad,
          umbral: producto?.umbral_minimo ?? null,
          almacen: existencia.almacen_nombre,
        }
      }),
    [existencias, productosPorId],
  )

  const filasMovimientos = useMemo<FilaMovimiento[]>(
    () =>
      movimientos.map((movimiento) => ({
        id: movimiento.id,
        fecha: movimiento.fecha,
        producto: productosPorId.get(movimiento.producto_id)?.nombre ?? 'Producto no disponible',
        tipo: movimiento.tipo,
        referenciaTipo: movimiento.referencia_tipo,
        cantidad: movimiento.cantidad,
        nota: movimiento.nota,
      })),
    [movimientos, productosPorId],
  )

  const confirmarAjuste = async () => {
    if (ajuste === null || procesando) return
    const delta = Number.parseInt(deltaTexto, 10)
    if (!Number.isFinite(delta) || delta === 0) {
      notificar('Escribe una cantidad distinta de cero (positivo suma, negativo resta).', 'error')
      return
    }
    if (nota.trim() === '') {
      notificar('Escribe una nota que explique el ajuste.', 'error')
      return
    }
    setProcesando(true)
    try {
      await ajustarExistencia({
        producto_id: ajuste.productoId,
        cantidad: delta,
        nota: nota.trim(),
      })
      notificar('Existencia ajustada.', 'ok')
      setAjuste(null)
      setDeltaTexto('')
      setNota('')
      recargarExistencias()
      recargarMovimientos()
    } catch (fallo) {
      notificar(mensajeDeError(fallo), 'error')
    } finally {
      setProcesando(false)
    }
  }

  const cargando = cargandoExistencias || cargandoProductos
  const error = errorExistencias ?? errorProductos

  return (
    <div className="pagina">
      <div className="page-header">
        <div className="page-heading">
          <h1>Inventario</h1>
          <p className="page-sub">
            Existencia por producto y movimientos recientes. Los ajustes quedan registrados con su
            nota.
          </p>
        </div>
      </div>

      <section className="card">
        <div className="card-head">
          <h2>Existencias</h2>
        </div>

        {cargando && (
          <div>
            {[0, 1, 2, 3, 4].map((indice) => (
              <div key={indice} className="skeleton skeleton-row" />
            ))}
          </div>
        )}

        {!cargando && error !== null && (
          <div className="empty">
            <span className="empty-icon empty-icon-lucide" aria-hidden="true"><CircleAlert /></span>
            <h3>No se pudieron cargar las existencias</h3>
            <p>{error}</p>
            <Button
              variante="ghost"
              iconoIzquierdo={<RotateCcw aria-hidden="true" />}
              onClick={() => void recargarExistencias()}
            >
              Reintentar
            </Button>
          </div>
        )}

        {!cargando && error === null && filasExistencias.length === 0 && (
          <div className="empty tabla-vacia">
            <span className="empty-icon empty-icon-lucide" aria-hidden="true"><PackagePlus /></span>
            <h3>No hay existencias registradas</h3>
            <p>Cuando existan productos con existencia aparecerán aquí.</p>
          </div>
        )}

        {!cargando && error === null && filasExistencias.length > 0 && (
          <TablaExistencias
            filas={filasExistencias}
            puedeAjustar={puedeAjustar}
            onAjustar={(fila) => {
              setAjuste(fila)
              setDeltaTexto('')
              setNota('')
            }}
          />
        )}
      </section>

      {puedeVerMovimientos && (
        <section className="card">
          <div className="card-head">
            <h2>Movimientos recientes</h2>
          </div>

          {cargandoMovimientos && (
            <div>
              {[0, 1, 2, 3].map((indice) => (
                <div key={indice} className="skeleton skeleton-row" />
              ))}
            </div>
          )}

          {!cargandoMovimientos && errorMovimientos !== null && (
            <div className="empty">
              <span className="empty-icon empty-icon-lucide" aria-hidden="true"><CircleAlert /></span>
              <h3>No se pudieron cargar los movimientos</h3>
              <p>{errorMovimientos}</p>
              <Button
                variante="ghost"
                iconoIzquierdo={<RotateCcw aria-hidden="true" />}
                onClick={recargarMovimientos}
              >
                Reintentar
              </Button>
            </div>
          )}

          {!cargandoMovimientos && errorMovimientos === null && filasMovimientos.length === 0 && (
            <div className="empty tabla-vacia">
              <span className="empty-icon empty-icon-lucide" aria-hidden="true"><PackagePlus /></span>
              <h3>No hay movimientos registrados</h3>
              <p>Las entradas, salidas y ajustes aparecerán aquí.</p>
            </div>
          )}

          {!cargandoMovimientos && errorMovimientos === null && filasMovimientos.length > 0 && (
            <TablaMovimientos filas={filasMovimientos} />
          )}
        </section>
      )}

      <Dialogo
        abierto={ajuste !== null}
        titulo="Ajustar existencia"
        onCerrar={() => {
          if (!procesando) setAjuste(null)
        }}
        pie={
          <>
            <Button
              variante="ghost"
              iconoIzquierdo={<X aria-hidden="true" />}
              disabled={procesando}
              onClick={() => setAjuste(null)}
            >
              Cancelar
            </Button>
            <Button
              variante="primary"
              iconoIzquierdo={<Check aria-hidden="true" />}
              cargando={procesando}
              onClick={() => void confirmarAjuste()}
            >
              Aplicar ajuste
            </Button>
          </>
        }
      >
        {ajuste !== null && (
          <>
            <p className="detalle-meta">
              <strong>{ajuste.nombre}</strong> · {ajuste.codigo}
            </p>
            <div className="field">
              <label className="field-label" htmlFor="ajuste-cantidad">
                Cantidad a ajustar
              </label>
              <input
                id="ajuste-cantidad"
                className="input"
                inputMode="numeric"
                value={deltaTexto}
                onChange={(evento) => setDeltaTexto(evento.target.value)}
                placeholder="Positivo suma, negativo resta"
              />
              <p className="field-hint">
                Un valor positivo suma existencia (entrada); un valor negativo la resta (salida).
              </p>
            </div>
            <div className="field">
              <label className="field-label" htmlFor="ajuste-nota">Nota</label>
              <textarea
                id="ajuste-nota"
                className="input textarea"
                rows={3}
                value={nota}
                onChange={(evento) => setNota(evento.target.value)}
                placeholder="Explica el motivo del ajuste."
              />
            </div>
          </>
        )}
      </Dialogo>
    </div>
  )
}
