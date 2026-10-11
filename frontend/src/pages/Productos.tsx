import { useMemo, useState, type FormEvent } from 'react'
import { Check, CircleAlert, PackagePlus, Pencil, Plus, Power, RotateCcw, X } from 'lucide-react'
import type { ProductoRead } from '../api/types'
import { CAPACIDADES } from '../api/capacidades'
import { useCan } from '../auth/useCan'
import { Button } from '../components/ui/Button'
import { Dialogo } from '../components/ui/Dialogo'
import { DialogoConfirmacion } from '../components/ui/DialogoConfirmacion'
import { useToast } from '../components/ui/useToast'
import { useCategorias } from '../hooks/useCategorias'
import { useProductos } from '../hooks/useProductos'
import { useProveedores } from '../hooks/useProveedores'
import { mensajeDeError } from '../lib/errores'
import { formatCantidad, formatQ, parseDecimal } from '../lib/format'
import { actualizarProducto, crearProducto } from '../services/catalogo'

type FormularioProducto = {
  codigo: string
  nombre: string
  descripcion: string
  categoriaId: string
  proveedorId: string
  unidadMedida: string
  precioCosto: string
  precioVenta: string
  umbralMinimo: string
  diasVencimientoAviso: string
  fechaVencimiento: string
  fechaIngreso: string
  cantidadInicial: string
}

const FORMULARIO_VACIO: FormularioProducto = {
  codigo: '',
  nombre: '',
  descripcion: '',
  categoriaId: '',
  proveedorId: '',
  unidadMedida: 'unidad',
  precioCosto: '',
  precioVenta: '',
  umbralMinimo: '0',
  diasVencimientoAviso: '30',
  fechaVencimiento: '',
  fechaIngreso: '',
  cantidadInicial: '0',
}

function textoONulo(valor: string): string | null {
  const limpio = valor.trim()
  return limpio === '' ? null : limpio
}

function soloFecha(valor: string | null): string {
  return valor === null ? '' : valor.slice(0, 10)
}

function estadoExistencia(producto: ProductoRead): { etiqueta: string; clase: string } {
  const existencia = parseDecimal(producto.existencia) ?? 0
  const umbral = parseDecimal(producto.umbral_minimo) ?? 0
  if (existencia <= 0) return { etiqueta: 'Agotado', clase: 'pill-red' }
  if (existencia <= umbral) return { etiqueta: 'Stock bajo', clase: 'pill-amber' }
  return { etiqueta: 'Disponible', clase: 'pill-good' }
}

export function Productos() {
  const { notificar } = useToast()
  const puedeEditar = useCan(CAPACIDADES.productosEditar)
  const {
    productos,
    cargando,
    error,
    busqueda,
    setBusqueda,
    categoriaId,
    setCategoriaId,
    incluirInactivos,
    setIncluirInactivos,
    recargar,
  } = useProductos()
  const { categorias } = useCategorias(true)
  const { proveedores } = useProveedores(true)

  const nombreCategoria = useMemo(() => {
    const mapa = new Map<string, string>()
    for (const categoria of categorias) mapa.set(categoria.id, categoria.nombre)
    return mapa
  }, [categorias])

  const nombreProveedor = useMemo(() => {
    const mapa = new Map<string, string>()
    for (const proveedor of proveedores) mapa.set(proveedor.id, proveedor.nombre)
    return mapa
  }, [proveedores])

  const [dialogoAbierto, setDialogoAbierto] = useState(false)
  const [editando, setEditando] = useState<ProductoRead | null>(null)
  const [formulario, setFormulario] = useState<FormularioProducto>(FORMULARIO_VACIO)
  const [guardando, setGuardando] = useState(false)
  const [aCambiarEstado, setACambiarEstado] = useState<ProductoRead | null>(null)
  const [procesando, setProcesando] = useState(false)

  const abrirCrear = () => {
    setEditando(null)
    setFormulario(FORMULARIO_VACIO)
    setDialogoAbierto(true)
  }

  const abrirEditar = (producto: ProductoRead) => {
    setEditando(producto)
    setFormulario({
      codigo: producto.codigo,
      nombre: producto.nombre,
      descripcion: producto.descripcion ?? '',
      categoriaId: producto.categoria_id,
      proveedorId: producto.proveedor_id ?? '',
      unidadMedida: producto.unidad_medida,
      precioCosto: producto.precio_costo,
      precioVenta: producto.precio_venta,
      umbralMinimo: producto.umbral_minimo,
      diasVencimientoAviso: String(producto.dias_vencimiento_aviso),
      fechaVencimiento: soloFecha(producto.fecha_vencimiento),
      fechaIngreso: soloFecha(producto.fecha_ingreso),
      cantidadInicial: '0',
    })
    setDialogoAbierto(true)
  }

  const validar = (): string | null => {
    if (editando === null && formulario.codigo.trim() === '') return 'El código es obligatorio.'
    if (formulario.nombre.trim() === '') return 'El nombre es obligatorio.'
    if (formulario.categoriaId === '') return 'Selecciona una categoría.'
    if (parseDecimal(formulario.precioVenta) === null) return 'El precio de venta debe ser un número válido.'
    if (parseDecimal(formulario.precioCosto) === null) return 'El precio de costo debe ser un número válido.'
    if (parseDecimal(formulario.umbralMinimo) === null) return 'El umbral mínimo debe ser un número válido.'
    const dias = Number(formulario.diasVencimientoAviso)
    if (!Number.isInteger(dias) || dias < 0) return 'Los días de aviso deben ser un entero positivo.'
    if (editando === null && parseDecimal(formulario.cantidadInicial) === null) {
      return 'La cantidad inicial debe ser un número válido.'
    }
    return null
  }

  const guardar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    const problema = validar()
    if (problema !== null) {
      notificar(problema, 'error')
      return
    }
    setGuardando(true)
    try {
      const base = {
        nombre: formulario.nombre.trim(),
        descripcion: textoONulo(formulario.descripcion),
        categoria_id: formulario.categoriaId,
        proveedor_id: formulario.proveedorId === '' ? null : formulario.proveedorId,
        unidad_medida: formulario.unidadMedida.trim() === '' ? 'unidad' : formulario.unidadMedida.trim(),
        precio_venta: formulario.precioVenta.trim(),
        precio_costo: formulario.precioCosto.trim(),
        umbral_minimo: formulario.umbralMinimo.trim() === '' ? '0' : formulario.umbralMinimo.trim(),
        dias_vencimiento_aviso: Number(formulario.diasVencimientoAviso),
        fecha_vencimiento: textoONulo(formulario.fechaVencimiento),
        fecha_ingreso: textoONulo(formulario.fechaIngreso),
      }
      if (editando !== null) {
        await actualizarProducto(editando.id, base)
      } else {
        await crearProducto({
          ...base,
          codigo: formulario.codigo.trim(),
          cantidad_inicial: formulario.cantidadInicial.trim() === '' ? '0' : formulario.cantidadInicial.trim(),
        })
      }
      notificar(editando !== null ? 'Producto actualizado.' : 'Producto creado.', 'ok')
      setDialogoAbierto(false)
      await recargar()
    } catch (fallo) {
      notificar(mensajeDeError(fallo), 'error')
    } finally {
      setGuardando(false)
    }
  }

  const cambiarEstado = async () => {
    if (aCambiarEstado === null) return
    setProcesando(true)
    try {
      await actualizarProducto(aCambiarEstado.id, { activo: !aCambiarEstado.activo })
      notificar(aCambiarEstado.activo ? 'Producto desactivado.' : 'Producto reactivado.', 'ok')
      setACambiarEstado(null)
      await recargar()
    } catch (fallo) {
      notificar(mensajeDeError(fallo), 'error')
    } finally {
      setProcesando(false)
    }
  }

  const categoriasParaSelect = useMemo(() => {
    const activas = categorias.filter((categoria) => categoria.activo)
    if (
      editando !== null &&
      !activas.some((categoria) => categoria.id === editando.categoria_id) &&
      nombreCategoria.has(editando.categoria_id)
    ) {
      const actual = categorias.find((categoria) => categoria.id === editando.categoria_id)
      if (actual !== undefined) return [...activas, actual]
    }
    return activas
  }, [categorias, editando, nombreCategoria])

  const proveedoresParaSelect = useMemo(() => {
    const activos = proveedores.filter((proveedor) => proveedor.activo)
    if (
      editando !== null &&
      editando.proveedor_id !== null &&
      !activos.some((proveedor) => proveedor.id === editando.proveedor_id) &&
      nombreProveedor.has(editando.proveedor_id)
    ) {
      const actual = proveedores.find((proveedor) => proveedor.id === editando.proveedor_id)
      if (actual !== undefined) return [...activos, actual]
    }
    return activos
  }, [proveedores, editando, nombreProveedor])

  return (
    <div className="pagina">
      <div className="page-header">
        <div className="page-heading">
          <h1>Productos</h1>
          <p className="page-sub">Consulta y administra el catálogo de cosméticos del negocio.</p>
        </div>
        {puedeEditar && (
          <div className="page-actions">
            <Button variante="primary" iconoIzquierdo={<Plus aria-hidden="true" />} onClick={abrirCrear}>
              Nuevo producto
            </Button>
          </div>
        )}
      </div>

      <div className="toolbar">
        <div className="toolbar-search">
          <input
            className="input"
            type="search"
            value={busqueda}
            onChange={(evento) => setBusqueda(evento.target.value)}
            placeholder="Buscar por nombre o código…"
            aria-label="Buscar productos"
          />
        </div>
        <select
          className="select"
          value={categoriaId ?? ''}
          onChange={(evento) => setCategoriaId(evento.target.value === '' ? null : evento.target.value)}
          aria-label="Filtrar por categoría"
        >
          <option value="">Todas las categorías</option>
          {categorias
            .filter((categoria) => categoria.activo)
            .map((categoria) => (
              <option key={categoria.id} value={categoria.id}>
                {categoria.nombre}
              </option>
            ))}
        </select>
        <button
          type="button"
          className={`chip${incluirInactivos ? ' active' : ''}`}
          aria-pressed={incluirInactivos}
          onClick={() => setIncluirInactivos((valor) => !valor)}
        >
          Mostrar inactivos
        </button>
      </div>

      <div className="card">
        {cargando && (
          <div>
            {[0, 1, 2, 3].map((indice) => (
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
            <span className="empty-icon empty-icon-lucide" aria-hidden="true"><PackagePlus /></span>
            <h3>No hay productos que mostrar</h3>
            <p>
              {busqueda !== ''
                ? 'Ningún producto coincide con tu búsqueda.'
                : 'Cuando registres productos aparecerán aquí.'}
            </p>
          </div>
        )}

        {!cargando && error === null && productos.length > 0 && (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Producto</th>
                  <th scope="col">Categoría</th>
                  <th scope="col">Proveedor</th>
                  <th scope="col">Precio venta</th>
                  <th scope="col">Existencia</th>
                  <th scope="col">Estado</th>
                  {puedeEditar && <th scope="col" style={{ textAlign: 'right' }}>Acciones</th>}
                </tr>
              </thead>
              <tbody>
                {productos.map((producto) => {
                  const estado = estadoExistencia(producto)
                  return (
                    <tr key={producto.id}>
                      <td data-label="Producto">
                        <div className="cell-strong">{producto.nombre}</div>
                        <div className="cell-muted">{producto.codigo}</div>
                      </td>
                      <td data-label="Categoría" className="cell-muted">
                        {nombreCategoria.get(producto.categoria_id) ?? '—'}
                      </td>
                      <td data-label="Proveedor" className="cell-muted">
                        {producto.proveedor_id === null
                          ? '—'
                          : nombreProveedor.get(producto.proveedor_id) ?? '—'}
                      </td>
                      <td data-label="Precio venta" className="num">
                        {formatQ(producto.precio_venta)}
                      </td>
                      <td data-label="Existencia" className="num">
                        {formatCantidad(producto.existencia)} {producto.unidad_medida}
                      </td>
                      <td data-label="Estado">
                        <span className={`pill ${estado.clase}`}>{estado.etiqueta}</span>
                      </td>
                      {puedeEditar && (
                        <td data-label="Acciones">
                          <div className="row-actions">
                            <button
                              type="button"
                              className="btn btn-ghost btn-sm"
                              onClick={() => abrirEditar(producto)}
                            >
                              <span className="btn-icono" aria-hidden="true"><Pencil /></span> Editar
                            </button>
                            <button
                              type="button"
                              className="btn btn-ghost btn-sm"
                              onClick={() => setACambiarEstado(producto)}
                            >
                              <span className="btn-icono" aria-hidden="true"><Power /></span> {producto.activo ? 'Desactivar' : 'Reactivar'}
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Dialogo
        abierto={dialogoAbierto}
        titulo={editando !== null ? 'Editar producto' : 'Nuevo producto'}
        onCerrar={() => setDialogoAbierto(false)}
        pie={
          <>
            <Button
              variante="ghost"
              iconoIzquierdo={<X aria-hidden="true" />}
              onClick={() => setDialogoAbierto(false)}
              disabled={guardando}
            >
              Cancelar
            </Button>
            <Button
              variante="primary"
              iconoIzquierdo={<Check aria-hidden="true" />}
              cargando={guardando}
              type="submit"
              form="form-producto"
            >
              Guardar
            </Button>
          </>
        }
      >
        <form id="form-producto" className="form-grid" onSubmit={guardar}>
          {editando === null && (
            <div className="field">
              <label className="field-label" htmlFor="producto-codigo">Código</label>
              <input
                id="producto-codigo"
                className="input"
                value={formulario.codigo}
                onChange={(evento) =>
                  setFormulario((actual) => ({ ...actual, codigo: evento.target.value }))
                }
                placeholder="Ej. LAB-001"
              />
            </div>
          )}
          <div className={`field${editando === null ? '' : ' span-2'}`}>
            <label className="field-label" htmlFor="producto-nombre">Nombre</label>
            <input
              id="producto-nombre"
              className="input"
              value={formulario.nombre}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, nombre: evento.target.value }))
              }
              placeholder="Ej. Labial mate rosa"
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="producto-categoria">Categoría</label>
            <select
              id="producto-categoria"
              className="select"
              value={formulario.categoriaId}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, categoriaId: evento.target.value }))
              }
            >
              <option value="">Selecciona…</option>
              {categoriasParaSelect.map((categoria) => (
                <option key={categoria.id} value={categoria.id}>
                  {categoria.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label className="field-label" htmlFor="producto-proveedor">Proveedor</label>
            <select
              id="producto-proveedor"
              className="select"
              value={formulario.proveedorId}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, proveedorId: evento.target.value }))
              }
            >
              <option value="">Sin proveedor</option>
              {proveedoresParaSelect.map((proveedor) => (
                <option key={proveedor.id} value={proveedor.id}>
                  {proveedor.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label className="field-label" htmlFor="producto-unidad">Unidad de medida</label>
            <input
              id="producto-unidad"
              className="input"
              value={formulario.unidadMedida}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, unidadMedida: evento.target.value }))
              }
              placeholder="unidad, caja, ml…"
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="producto-precio-costo">Precio de costo (Q)</label>
            <input
              id="producto-precio-costo"
              className="input"
              inputMode="decimal"
              value={formulario.precioCosto}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, precioCosto: evento.target.value }))
              }
              placeholder="0.00"
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="producto-precio-venta">Precio de venta (Q)</label>
            <input
              id="producto-precio-venta"
              className="input"
              inputMode="decimal"
              value={formulario.precioVenta}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, precioVenta: evento.target.value }))
              }
              placeholder="0.00"
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="producto-umbral">Umbral mínimo de stock</label>
            <input
              id="producto-umbral"
              className="input"
              inputMode="decimal"
              value={formulario.umbralMinimo}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, umbralMinimo: evento.target.value }))
              }
              placeholder="0"
            />
            <span className="field-hint">Se avisará cuando la existencia llegue a este valor.</span>
          </div>
          <div className="field">
            <label className="field-label" htmlFor="producto-dias-aviso">Días de aviso por vencimiento</label>
            <input
              id="producto-dias-aviso"
              className="input"
              inputMode="numeric"
              value={formulario.diasVencimientoAviso}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, diasVencimientoAviso: evento.target.value }))
              }
              placeholder="30"
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="producto-fecha-vencimiento">Fecha de vencimiento</label>
            <input
              id="producto-fecha-vencimiento"
              className="input"
              type="date"
              value={formulario.fechaVencimiento}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, fechaVencimiento: evento.target.value }))
              }
            />
            <span className="field-hint">Déjala vacía si el producto no perece.</span>
          </div>
          <div className="field">
            <label className="field-label" htmlFor="producto-fecha-ingreso">Fecha de ingreso</label>
            <input
              id="producto-fecha-ingreso"
              className="input"
              type="date"
              value={formulario.fechaIngreso}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, fechaIngreso: evento.target.value }))
              }
            />
          </div>
          {editando === null && (
            <div className="field">
              <label className="field-label" htmlFor="producto-cantidad-inicial">Cantidad inicial</label>
              <input
                id="producto-cantidad-inicial"
                className="input"
                inputMode="decimal"
                value={formulario.cantidadInicial}
                onChange={(evento) =>
                  setFormulario((actual) => ({ ...actual, cantidadInicial: evento.target.value }))
                }
                placeholder="0"
              />
            </div>
          )}
          <div className="field span-2">
            <label className="field-label" htmlFor="producto-descripcion">Descripción</label>
            <textarea
              id="producto-descripcion"
              className="textarea"
              value={formulario.descripcion}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, descripcion: evento.target.value }))
              }
              placeholder="Opcional"
            />
          </div>
        </form>
      </Dialogo>

      <DialogoConfirmacion
        abierto={aCambiarEstado !== null}
        titulo={aCambiarEstado?.activo === true ? 'Desactivar producto' : 'Reactivar producto'}
        mensaje={
          aCambiarEstado?.activo === true
            ? 'El producto dejará de aparecer en las listas activas. Podrás reactivarlo después.'
            : 'El producto volverá a estar disponible en el catálogo.'
        }
        textoConfirmar={aCambiarEstado?.activo === true ? 'Desactivar' : 'Reactivar'}
        peligroso={aCambiarEstado?.activo === true}
        ocupado={procesando}
        onConfirmar={() => void cambiarEstado()}
        onCerrar={() => setACambiarEstado(null)}
      />
    </div>
  )
}
