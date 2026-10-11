import { Link } from 'react-router'
import { useAlertas } from '../../hooks/useAlertas'
import { formatCantidad } from '../../lib/format'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'
import type { AlertaStockBajo, AlertaVencimientoProximo } from '../../api/types'

type FilaAlerta =
  | { tipo: 'agotado' | 'bajo'; id: string; nombre: string; cantidad: number }
  | { tipo: 'vencido' | 'proximo'; id: string; nombre: string; cantidad: number }

function filasDeAlerta(
  bajos: AlertaStockBajo[],
  vencimientos: AlertaVencimientoProximo[],
): FilaAlerta[] {
  const filas: FilaAlerta[] = [
    ...bajos.map((a): FilaAlerta => ({
      tipo: a.agotado ? 'agotado' : 'bajo',
      id: a.producto_id,
      nombre: a.nombre,
      cantidad: Number(a.existencia),
    })),
    ...vencimientos.map((v): FilaAlerta => ({
      tipo: v.vencido ? 'vencido' : 'proximo',
      id: v.producto_id,
      nombre: v.nombre,
      cantidad: v.dias_restantes ?? 0,
    })),
  ]
  return filas.slice(0, 4)
}

function ContenidoAlertas({
  alertas,
  enlace,
}: {
  alertas: { bajo_stock: AlertaStockBajo[]; vencimiento_proximo: AlertaVencimientoProximo[] } | null
  enlace?: string
}) {
  return (
    <>
      {alertas !== null && (
        <div className="panel-metricas panel-metricas-chicas">
          <div className="panel-metrica">
            <span className="panel-metrica-etiqueta">Stock bajo</span>
            <span className="panel-metrica-valor">
              {formatCantidad(alertas.bajo_stock.length)}
            </span>
          </div>
          <div className="panel-metrica">
            <span className="panel-metrica-etiqueta">Por vencer / vencido</span>
            <span className="panel-metrica-valor">
              {formatCantidad(alertas.vencimiento_proximo.length)}
            </span>
          </div>
        </div>
      )}
      {alertas !== null && (
        <ul className="panel-lista">
          {filasDeAlerta(alertas.bajo_stock, alertas.vencimiento_proximo).map((fila) => (
            <li key={`${fila.tipo}-${fila.id}`} className="panel-fila">
              <span className="texto-cortado">{fila.nombre}</span>
              <span className={`pill pill-${fila.tipo}`}>
                {fila.tipo === 'agotado'
                  ? 'Agotado'
                  : fila.tipo === 'bajo'
                    ? `Bajo (${formatCantidad(fila.cantidad)})`
                    : fila.tipo === 'vencido'
                      ? 'Vencido'
                      : `Faltan ${fila.cantidad} días`}
              </span>
            </li>
          ))}
        </ul>
      )}
      {enlace !== undefined && (
        <p className="panel-pie-enlace">
          <Link to={enlace}>Ver todas las alertas</Link>
        </p>
      )}
    </>
  )
}

export function TarjetaAlertas({ enlace }: { enlace?: string }) {
  const { alertas, cargando, error, recargar } = useAlertas()

  const vacio =
    alertas !== null && alertas.bajo_stock.length === 0 && alertas.vencimiento_proximo.length === 0

  return (
    <TarjetaPanel
      titulo="Alertas"
      enlace={enlace ?? '/alertas'}
      etiquetaEnlace="Revisar"
      hijos={
        <EstadoConsulta
          cargando={cargando}
          error={error}
          onReintentar={recargar}
          vacio={vacio}
          mensajeVacio="Sin alertas: el inventario está en orden."
          hijos={<ContenidoAlertas alertas={alertas} enlace={enlace} />}
        />
      }
    />
  )
}