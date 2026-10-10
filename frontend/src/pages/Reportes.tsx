import { useEffect, useState } from 'react'
import { CAPACIDADES } from '../api/capacidades'
import { RequireCapacidad } from '../auth/RequireCapacidad'
import { EstadoConsulta } from '../components/panel/EstadoConsulta'
import { useMasVendidos } from '../hooks/useMasVendidos'
import { formatCantidad, formatQ } from '../lib/format'
import { haceDiasISO, hoyISO } from '../lib/fecha'

export function Reportes() {
  const [diasVentana, setDiasVentana] = useState(30)
  const fechaInicioDefault = haceDiasISO(diasVentana - 1)
  const fechaFinDefault = hoyISO()
  const [fechaInicio, setFechaInicio] = useState(fechaInicioDefault)
  const [fechaFin, setFechaFin] = useState(fechaFinDefault)
  const { items, cargando, error, recargar } = useMasVendidos(50, diasVentana)
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    setFechaInicio(haceDiasISO(diasVentana - 1))
    setFechaFin(hoyISO())
  }, [diasVentana])
/* eslint-enable react-hooks/set-state-in-effect */

  const maximo = Math.max(0, ...items.map((i) => i.cantidad_vendida))

  return (
    <RequireCapacidad capacidad={CAPACIDADES.reportesVer}>
      <div className="pagina">
        <div className="page-header">
          <div>
            <h1>Reportes</h1>
            <p className="page-subtitle">Productos más vendidos por periodo.</p>
          </div>
        </div>
        <section className="card">
          <div className="card-pad card-filtros">
            <div className="filtro-grupo">
              <label htmlFor="ventana">Periodo</label>
              <select
                id="ventana"
                className="input"
                value={diasVentana}
                onChange={(e) => setDiasVentana(Number(e.target.value))}
              >
                <option value={7}>Últimos 7 días</option>
                <option value={30}>Últimos 30 días</option>
                <option value={60}>Últimos 60 días</option>
              </select>
            </div>
            <div className="filtro-grupo">
              <label htmlFor="inicio">Desde</label>
              <input
                id="inicio"
                className="input"
                type="date"
                value={fechaInicio}
                onChange={(e) => setFechaInicio(e.target.value)}
              />
            </div>
            <div className="filtro-grupo">
              <label htmlFor="fin">Hasta</label>
              <input
                id="fin"
                className="input"
                type="date"
                value={fechaFin}
                onChange={(e) => setFechaFin(e.target.value)}
              />
            </div>
            <button type="button" className="btn btn-ghost" onClick={recargar}>
              Aplicar
            </button>
          </div>
          <div className="table-wrap">
            <EstadoConsulta
              cargando={cargando}
              error={error}
              onReintentar={recargar}
              vacio={items.length === 0}
              mensajeVacio="No hay ventas en el periodo seleccionado."
            >
              <table className="data-table" aria-label="Productos más vendidos">
                <thead>
                  <tr>
                    <th>Producto</th>
                    <th>Código</th>
                    <th>Cantidad vendida</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item, idx) => {
                    const ancho = maximo > 0 ? (item.cantidad_vendida / maximo) * 100 : 0
                    return (
                      <tr key={item.producto_id}>
                        <td data-label="Producto">
                          {idx + 1}. {item.nombre}
                        </td>
                        <td data-label="Código">{item.codigo ?? '—'}</td>
                        <td data-label="Cantidad vendida">
                          {formatCantidad(item.cantidad_vendida)}
                          <div className="barra-horizontal">
                            <div className="barra-horizontal-fill" style={{ width: `${ancho}%` }} />
                          </div>
                        </td>
                        <td data-label="Total">{formatQ(item.total_vendido)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </EstadoConsulta>
          </div>
        </section>
      </div>
    </RequireCapacidad>
  )
}