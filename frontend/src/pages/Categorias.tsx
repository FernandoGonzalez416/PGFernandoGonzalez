import { useState, type FormEvent } from 'react'
import { Check, CircleAlert, PackagePlus, Pencil, Plus, Power, RotateCcw, X } from 'lucide-react'
import type { CategoriaRead } from '../api/types'
import { Button } from '../components/ui/Button'
import { Dialogo } from '../components/ui/Dialogo'
import { DialogoConfirmacion } from '../components/ui/DialogoConfirmacion'
import { useToast } from '../components/ui/useToast'
import { useCategorias } from '../hooks/useCategorias'
import { mensajeDeError } from '../lib/errores'
import { actualizarCategoria, crearCategoria } from '../services/catalogo'

type FormularioCategoria = { nombre: string; descripcion: string }

const FORMULARIO_VACIO: FormularioCategoria = { nombre: '', descripcion: '' }

export function Categorias() {
  const { notificar } = useToast()
  const [incluirInactivas, setIncluirInactivas] = useState(false)
  const { categorias, cargando, error, recargar } = useCategorias(incluirInactivas)

  const [dialogoAbierto, setDialogoAbierto] = useState(false)
  const [editando, setEditando] = useState<CategoriaRead | null>(null)
  const [formulario, setFormulario] = useState<FormularioCategoria>(FORMULARIO_VACIO)
  const [guardando, setGuardando] = useState(false)
  const [aCambiarEstado, setACambiarEstado] = useState<CategoriaRead | null>(null)
  const [procesando, setProcesando] = useState(false)

  const abrirCrear = () => {
    setEditando(null)
    setFormulario(FORMULARIO_VACIO)
    setDialogoAbierto(true)
  }

  const abrirEditar = (categoria: CategoriaRead) => {
    setEditando(categoria)
    setFormulario({ nombre: categoria.nombre, descripcion: categoria.descripcion ?? '' })
    setDialogoAbierto(true)
  }

  const guardar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    if (formulario.nombre.trim() === '') {
      notificar('El nombre de la categoría es obligatorio.', 'error')
      return
    }
    setGuardando(true)
    try {
      const descripcion = formulario.descripcion.trim()
      const datos = {
        nombre: formulario.nombre.trim(),
        descripcion: descripcion === '' ? null : descripcion,
      }
      if (editando !== null) await actualizarCategoria(editando.id, datos)
      else await crearCategoria(datos)
      notificar(editando !== null ? 'Categoría actualizada.' : 'Categoría creada.', 'ok')
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
      await actualizarCategoria(aCambiarEstado.id, { activo: !aCambiarEstado.activo })
      notificar(aCambiarEstado.activo ? 'Categoría desactivada.' : 'Categoría reactivada.', 'ok')
      setACambiarEstado(null)
      await recargar()
    } catch (fallo) {
      notificar(mensajeDeError(fallo), 'error')
    } finally {
      setProcesando(false)
    }
  }

  return (
    <div className="pagina">
      <div className="page-header">
        <div className="page-heading">
          <h1>Categorías</h1>
          <p className="page-sub">Organiza los productos del catálogo por tipo de cosmético.</p>
        </div>
        <div className="page-actions">
          <Button variante="primary" iconoIzquierdo={<Plus aria-hidden="true" />} onClick={abrirCrear}>
            Nueva categoría
          </Button>
        </div>
      </div>

      <div className="toolbar">
        <button
          type="button"
          className={`chip${incluirInactivas ? ' active' : ''}`}
          aria-pressed={incluirInactivas}
          onClick={() => setIncluirInactivas((valor) => !valor)}
        >
          Mostrar inactivas
        </button>
      </div>

      <div className="card">
        {cargando && (
          <div>
            {[0, 1, 2].map((indice) => (
              <div key={indice} className="skeleton skeleton-row" />
            ))}
          </div>
        )}

        {!cargando && error !== null && (
          <div className="empty">
            <span className="empty-icon empty-icon-lucide" aria-hidden="true"><CircleAlert /></span>
            <h3>No se pudieron cargar las categorías</h3>
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

        {!cargando && error === null && categorias.length === 0 && (
          <div className="empty tabla-vacia">
            <span className="empty-icon empty-icon-lucide" aria-hidden="true"><PackagePlus /></span>
            <h3>Aún no hay categorías</h3>
            <p>Crea la primera categoría para empezar a clasificar tus productos.</p>
          </div>
        )}

        {!cargando && error === null && categorias.length > 0 && (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Categoría</th>
                  <th scope="col">Descripción</th>
                  <th scope="col">Estado</th>
                  <th scope="col" style={{ textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {categorias.map((categoria) => (
                  <tr key={categoria.id}>
                    <td data-label="Categoría" className="cell-strong">{categoria.nombre}</td>
                    <td data-label="Descripción" className="cell-muted">
                      {categoria.descripcion ?? '—'}
                    </td>
                    <td data-label="Estado">
                      <span className={`pill ${categoria.activo ? 'pill-good' : 'pill-neutral'}`}>
                        {categoria.activo ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    <td data-label="Acciones">
                      <div className="row-actions">
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => abrirEditar(categoria)}
                        >
                          <span className="btn-icono" aria-hidden="true"><Pencil /></span> Editar
                        </button>
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => setACambiarEstado(categoria)}
                        >
                          <span className="btn-icono" aria-hidden="true"><Power /></span> {categoria.activo ? 'Desactivar' : 'Reactivar'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Dialogo
        abierto={dialogoAbierto}
        titulo={editando !== null ? 'Editar categoría' : 'Nueva categoría'}
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
              form="form-categoria"
            >
              Guardar
            </Button>
          </>
        }
      >
        <form id="form-categoria" className="form-grid" onSubmit={guardar}>
          <div className="field span-2">
            <label className="field-label" htmlFor="categoria-nombre">Nombre</label>
            <input
              id="categoria-nombre"
              className="input"
              value={formulario.nombre}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, nombre: evento.target.value }))
              }
              placeholder="Ej. Maquillaje"
            />
          </div>
          <div className="field span-2">
            <label className="field-label" htmlFor="categoria-descripcion">Descripción</label>
            <textarea
              id="categoria-descripcion"
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
        titulo={aCambiarEstado?.activo === true ? 'Desactivar categoría' : 'Reactivar categoría'}
        mensaje={
          aCambiarEstado?.activo === true
            ? 'La categoría dejará de estar disponible al registrar productos nuevos. Podrás reactivarla después.'
            : 'La categoría volverá a estar disponible para registrar productos.'
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
