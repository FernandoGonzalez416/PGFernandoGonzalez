import { useMemo } from 'react'
import { Eye, RotateCcw } from 'lucide-react'
import { Link } from 'react-router'
import { CAPACIDADES } from '../api/capacidades'
import { RequireCapacidad } from '../auth/RequireCapacidad'
import { EstadoConsulta } from '../components/panel/EstadoConsulta'
import { Button } from '../components/ui/Button'
import { useAlertas } from '../hooks/useAlertas'
import { formatCantidad, formatFecha } from '../lib/format'
import type { AlertaStockBajo, AlertaVencimientoProximo } from '../api/types'

type Fila =
  | { tipo: 'agotado' | 'bajo'; producto_id: string; codigo?: string | null; nombre: string; existencia: number; umbral_minimo?: number }
  | { tipo: 'vencido' | 'proximo'; producto_id: string; codigo?: string | null; nombre: string; fecha_vencimiento: string | null; dias_restantes: number | null }

function obtenerFilas(
  bajos: AlertaStockBajo[],
  vencimientos: AlertaVencimientoProximo[],
): Fila[] {
  return [
    ...bajos.map((a): Fila => ({
      tipo: a.agotado ? 'agotado' : 'bajo',
      producto_id: a.producto_id,
      codigo: a.codigo ?? null,
      nombre: a.nombre,
      existencia: Number(a.existencia),
      umbral_minimo: a.umbral_minimo !== undefined ? Number(a.umbral_minimo) : undefined,
    })),
    ...vencimientos.map((v): Fila => ({
      tipo: v.vencido ? 'vencido' : 'proximo',
      producto_id: v.producto_id,
      codigo: v.codigo ?? null,
      nombre: v.nombre,
      fecha_vencimiento: v.fecha_vencimiento,
      dias_restantes: v.dias_restantes,
    })),
  ]
}

export function Alertas() {
  const { alertas, cargando, error, recargar } = useAlertas()
  const filas = useMemo(() => {
    if (alertas === null) return []
    return obtenerFilas(alertas.bajo_stock, alertas.vencimiento_proximo)
  }, [alertas])

  const vacio = filas.length === 0

  const contenido = (
  <table className="data-table" aria-label="Alertas">
    <thead>
      <tr>
        <th>Producto</th>
        <th>Código</th>
        <th>Estado</th>
        <th>Detalle</th>
        <th>Ver</th>
      </tr>
    </thead>
    <tbody>
      {filas.map((fila) => (
        <tr key={`${fila.tipo}-${fila.producto_id}`}>
          <td data-label="Producto">{fila.nombre}</td>
          <td data-label="Código">{fila.codigo ?? '—'}</td>
          <td data-label="Estado">
            <span className={`pill pill-${fila.tipo}`}>
              {fila.tipo === 'agotado'
                ? 'Agotado'
                : fila.tipo === 'bajo'
                  ? 'Bajo'
                  : fila.tipo === 'vencido'
                    ? 'Vencido'
                    : 'Por vencer'}
            </span>
          </td>
          <td data-label="Detalle">
            {fila.tipo === 'agotado' && <>Existencia: {formatCantidad(fila.existencia)} · Umbral: {formatCantidad(fila.umbral_minimo)}</>}
            {fila.tipo === 'bajo' && <>Existencia: {formatCantidad(fila.existencia)} · Umbral: {formatCantidad(fila.umbral_minimo)}</>}
            {fila.tipo === 'vencido' && <>Vence: {formatFecha(fila.fecha_vencimiento)} · {(fila.dias_restantes ?? 0) <= 0 ? 'Vencido' : `Faltan ${formatCantidad(fila.dias_restantes)} días`}</>}
            {fila.tipo === 'proximo' && <>Vence: {formatFecha(fila.fecha_vencimiento)} · Faltan {formatCantidad(fila.dias_restantes)} días</>}
          </td>
          <td data-label="Ver">
            <Link to="/productos" className="btn btn-ghost btn-sm"><span className="btn-icono" aria-hidden="true"><Eye /></span> Ver producto</Link>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
)

return (
  <RequireCapacidad capacidad={CAPACIDADES.alertasVer}>
    <div className="pagina">
      <div className="page-header">
        <div>
          <h1>Alertas de inventario</h1>
          <p className="page-subtitle">Stock bajo, productos agotados y vencimientos próximos o vencidos.</p>
        </div>
        <div className="page-header-acciones">
          <Button
            variante="ghost"
            iconoIzquierdo={<RotateCcw aria-hidden="true" />}
            onClick={recargar}
          >
            Actualizar
          </Button>
        </div>
      </div>
      <section className="card">
        <div className="table-wrap">
          <EstadoConsulta
            cargando={cargando}
            error={error}
            onReintentar={recargar}
            vacio={vacio}
            mensajeVacio="Sin alertas en este momento."
            hijos={contenido}
          />
        </div>
      </section>
    </div>
  </RequireCapacidad>
)
}