import { useMemo, useState, type KeyboardEvent } from 'react'
import { Banknote, CircleAlert, PackagePlus, Plus, RotateCcw, SearchX, Trash2 } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { useNavigate } from 'react-router'
import { useToast } from '../components/ui/useToast'
import { Button } from '../components/ui/Button'
import { mensajeDeError } from '../lib/errores'
import { formatCantidad, formatQ } from '../lib/format'
import {
  aCentavos,
  agregarLinea,
  cantidadDisponible,
  centavosAQ,
  quitarLinea,
  cambiarCantidad,
  totalesCarrito,
  type LineaCarrito,
} from '../lib/carrito'
import { useProductos } from '../hooks/useProductos'
import { registrarVenta } from '../services/ventas'
import { TablaCarrito } from '../components/ventas/TablaCarrito'

const METODOS = [
  { valor: 'efectivo', etiqueta: 'Efectivo' },
  { valor: 'tarjeta', etiqueta: 'Tarjeta' },
  { valor: 'transferencia', etiqueta: 'Transferencia' },
  { valor: 'otro', etiqueta: 'Otro' },
] as const

type MetodoPago = (typeof METODOS)[number]['valor']

function esMetodoPago(valor: string): valor is MetodoPago {
  return METODOS.some((metodo) => metodo.valor === valor)
}

export function VentaNueva() {
  const { notificar } = useToast()
  const navegar = useNavigate()
  const { productos, cargando, error, busqueda, setBusqueda, recargar } = useProductos()
  const reducirMovimiento = useReducedMotion()

  const [lineas, setLineas] = useState<LineaCarrito[]>([])
  const [descuentoTexto, setDescuentoTexto] = useState('')
  const [metodoPago, setMetodoPago] = useState<MetodoPago>('efectivo')
  const [enviando, setEnviando] = useState(false)

  const totales = useMemo(
    () => totalesCarrito(lineas, aCentavos(descuentoTexto)),
    [lineas, descuentoTexto],
  )

  const agregar = (indice: number) => {
    const producto = productos[indice]
    if (producto === undefined) return
    if (cantidadDisponible(producto) <= 0) {
      notificar(`${producto.nombre} no tiene existencia disponible.`, 'error')
      return
    }
    setLineas((actual) => agregarLinea(actual, producto))
  }

  const alPresionarEnter = (evento: KeyboardEvent<HTMLInputElement>) => {
    if (evento.key !== 'Enter') return
    evento.preventDefault()
    const codigo = busqueda.trim().toLowerCase()
    if (codigo === '') return
    const indice = productos.findIndex((producto) => producto.codigo.toLowerCase() === codigo)
    if (indice === -1) {
      notificar('No se encontró un producto con ese código.', 'error')
      return
    }
    agregar(indice)
    setBusqueda('')
  }

  const cobrar = async () => {
    if (lineas.length === 0 || enviando) return
    setEnviando(true)
    try {
      const venta = await registrarVenta({
        lineas: lineas.map((linea) => ({ producto_id: linea.productoId, cantidad: linea.cantidad })),
        descuento: centavosAQ(totales.descuentoCents),
        metodo_pago: metodoPago,
        cliente_id: null,
      })
      notificar('Venta registrada.', 'ok')
      navegar(`/ventas/${venta.id}/recibo`)
    } catch (fallo) {
      notificar(mensajeDeError(fallo), 'error')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="pagina venta-nueva">
      <div className="page-header">
        <div className="page-heading">
          <h1>Nueva venta</h1>
          <p className="page-sub">
            Agrega productos y cobra. La existencia se descuenta al registrar la venta.
          </p>
        </div>
      </div>

      <div className="pos-grid">
        <section className="card card-pad pos-busqueda">
          <div className="field">
            <label className="field-label" htmlFor="pos-buscar">Buscar producto</label>
            <input
              id="pos-buscar"
              className="input"
              autoFocus
              value={busqueda}
              onChange={(evento) => setBusqueda(evento.target.value)}
              onKeyDown={alPresionarEnter}
              placeholder="Código o nombre… escanea y pulsa Enter"
            />
          </div>

          <div className="pos-resultados-wrap">
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
                <h3>No se pudieron cargar los productos</h3>
                <p>{error}</p>
                <Button
                  variante="ghost"
                  iconoIzquierdo={<RotateCcw aria-hidden="true" />}
                  onClick={() => void recargar()}
                >
                  Reintentar
                </Button>
              </div>
            )}

            {!cargando && error === null && productos.length === 0 && (
              <div className="empty tabla-vacia">
                <span className="empty-icon empty-icon-lucide" aria-hidden="true"><SearchX /></span>
                <h3>No hay productos que coincidan</h3>
                <p>Prueba con otro código o nombre.</p>
              </div>
            )}

            {!cargando && error === null && productos.length > 0 && (
              <ul className="pos-resultados">
                {productos.map((producto, indice) => (
                  <motion.li
                    key={producto.id}
                    initial={reducirMovimiento === true ? false : { opacity: 0, transform: 'translateY(6px)' }}
                    animate={{ opacity: 1, transform: 'translateY(0px)' }}
                    transition={{
                      duration: 0.25,
                      delay: Math.min(indice, 10) * 0.03,
                      ease: [0.23, 1, 0.32, 1],
                    }}
                  >
                    <button
                      type="button"
                      className="pos-resultado"
                      disabled={cantidadDisponible(producto) <= 0}
                      onClick={() => agregar(indice)}
                    >
                      <span className="pos-resultado-info">
                        <span className="cell-strong">{producto.nombre}</span>
                        <span className="cell-muted">
                          {producto.codigo} · {formatCantidad(producto.existencia)}{' '}
                          {producto.unidad_medida}
                        </span>
                      </span>
                      <span className="pos-resultado-precio">
                        <span className="num">{formatQ(producto.precio_venta)}</span>
                        <span className="btn-icono" aria-hidden="true"><Plus /></span>
                      </span>
                    </button>
                  </motion.li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <section className="card pos-carrito">
          <div className="pos-carrito-head">
            <h2>Carrito</h2>
            <div className="pos-carrito-head-lado">
              <span className="pill pill-neutral num">
                {lineas.length} {lineas.length === 1 ? 'artículo' : 'artículos'}
              </span>
              {lineas.length > 0 && (
                <Button
                  variante="ghost"
                  tamano="sm"
                  iconoIzquierdo={<Trash2 aria-hidden="true" />}
                  aria-label="Vaciar carrito"
                  onClick={() => setLineas([])}
                >
                  Vaciar
                </Button>
              )}
            </div>
          </div>

          {lineas.length === 0 ? (
            <div className="empty pos-vacio">
              <span className="empty-icon empty-icon-lucide" aria-hidden="true"><PackagePlus /></span>
              <h3>Aún no hay productos</h3>
              <p>Busca un producto y agrégalo al carrito para cobrar.</p>
            </div>
          ) : (
            <TablaCarrito
              lineas={lineas}
              totales={totales}
              onCambiarCantidad={(productoId, cantidad) =>
                setLineas((actual) => cambiarCantidad(actual, productoId, cantidad))
              }
              onQuitar={(productoId) => setLineas((actual) => quitarLinea(actual, productoId))}
            />
          )}

          <div className="pos-cobro">
            <div className="pos-cobro-campos">
              <div className="field">
                <label className="field-label" htmlFor="pos-descuento">Descuento (Q)</label>
                <input
                  id="pos-descuento"
                  className="input"
                  inputMode="decimal"
                  value={descuentoTexto}
                  onChange={(evento) => setDescuentoTexto(evento.target.value)}
                  placeholder="0.00"
                />
              </div>
              <div className="field">
                <label className="field-label" htmlFor="pos-metodo">Método de pago</label>
                <select
                  id="pos-metodo"
                  className="select"
                  value={metodoPago}
                  onChange={(evento) => {
                    const valor = evento.target.value
                    if (esMetodoPago(valor)) setMetodoPago(valor)
                  }}
                >
                  {METODOS.map((metodo) => (
                    <option key={metodo.valor} value={metodo.valor}>
                      {metodo.etiqueta}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <Button
              variante="primary"
              bloque
              cargando={enviando}
              disabled={lineas.length === 0 || enviando}
              iconoIzquierdo={<Banknote aria-hidden="true" />}
              onClick={() => void cobrar()}
            >
              {`Cobrar ${formatQ(totales.totalCents / 100)}`}
            </Button>
          </div>
        </section>
      </div>
    </div>
  )
}
