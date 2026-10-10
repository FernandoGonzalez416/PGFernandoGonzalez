import { useSugerencias } from '../../hooks/useSugerencias'
import { formatCantidad } from '../../lib/format'
import { EstadoConsulta } from './EstadoConsulta'
import { TarjetaPanel } from './TarjetaPanel'

export function TarjetaSugerencias({ enlace }: { enlace?: string }) {
  const { sugerencias, total, cargando, error, recargar } = useSugerencias(5)

  return (
    <TarjetaPanel titulo="Sugerencias de compra" enlace={enlace ?? '/sugerencias'}>
      <EstadoConsulta
        cargando={cargando}
        error={error}
        onReintentar={recargar}
        vacio={sugerencias.length === 0}
        mensajeVacio="No hay sugerencias pendientes."
      >
        <p className="panel-metrica-contexto panel-en-linea">
          {total} pendiente(s) por revisar
        </p>
        <ul className="panel-lista">
          {sugerencias.map((sugerencia) => (
            <li key={sugerencia.id} className="panel-fila">
              <span className="texto-cortado">{sugerencia.nombre ?? sugerencia.codigo}</span>
              <span className={`pill pill-prioridad-${sugerencia.prioridad}`}>
                {formatCantidad(sugerencia.cantidad_sugerida)} · {sugerencia.prioridad}
              </span>
            </li>
          ))}
        </ul>
      </EstadoConsulta>
    </TarjetaPanel>
  )
}