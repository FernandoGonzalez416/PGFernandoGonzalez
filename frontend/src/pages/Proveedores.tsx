import { useState, type FormEvent } from 'react'
import type { ProveedorRead } from '../api/types'
import { Dialogo } from '../components/ui/Dialogo'
import { DialogoConfirmacion } from '../components/ui/DialogoConfirmacion'
import { useToast } from '../components/ui/useToast'
import { useProveedores } from '../hooks/useProveedores'
import { mensajeDeError } from '../lib/errores'
import { formatQ, parseDecimal } from '../lib/format'
import { actualizarProveedor, crearProveedor } from '../services/catalogo'

type FormularioProveedor = {
  nombre: string
  contacto: string
  telefono: string
  email: string
  condicionesEntrega: string
  precioHabitual: string
}

const FORMULARIO_VACIO: FormularioProveedor = {
  nombre: '',
  contacto: '',
  telefono: '',
  email: '',
  condicionesEntrega: '',
  precioHabitual: '',
}

function textoONulo(valor: string): string | null {
  const limpio = valor.trim()
  return limpio === '' ? null : limpio
}

export function Proveedores() {
  const { notificar } = useToast()
  const [incluirInactivos, setIncluirInactivos] = useState(false)
  const { proveedores, cargando, error, recargar } = useProveedores(incluirInactivos)

  const [dialogoAbierto, setDialogoAbierto] = useState(false)
  const [editando, setEditando] = useState<ProveedorRead | null>(null)
  const [formulario, setFormulario] = useState<FormularioProveedor>(FORMULARIO_VACIO)
  const [guardando, setGuardando] = useState(false)
  const [aCambiarEstado, setACambiarEstado] = useState<ProveedorRead | null>(null)
  const [procesando, setProcesando] = useState(false)

  const abrirCrear = () => {
    setEditando(null)
    setFormulario(FORMULARIO_VACIO)
    setDialogoAbierto(true)
  }

  const abrirEditar = (proveedor: ProveedorRead) => {
    setEditando(proveedor)
    setFormulario({
      nombre: proveedor.nombre,
      contacto: proveedor.contacto ?? '',
      telefono: proveedor.telefono ?? '',
      email: proveedor.email ?? '',
      condicionesEntrega: proveedor.condiciones_entrega ?? '',
      precioHabitual: proveedor.precio_habitual ?? '',
    })
    setDialogoAbierto(true)
  }

  const guardar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    if (formulario.nombre.trim() === '') {
      notificar('El nombre del proveedor es obligatorio.', 'error')
      return
    }
    const precio = formulario.precioHabitual.trim()
    if (precio !== '' && parseDecimal(precio) === null) {
      notificar('El precio habitual debe ser un número válido.', 'error')
      return
    }
    setGuardando(true)
    try {
      const datos = {
        nombre: formulario.nombre.trim(),
        contacto: textoONulo(formulario.contacto),
        telefono: textoONulo(formulario.telefono),
        email: textoONulo(formulario.email),
        condiciones_entrega: textoONulo(formulario.condicionesEntrega),
        precio_habitual: precio === '' ? null : precio,
      }
      if (editando !== null) await actualizarProveedor(editando.id, datos)
      else await crearProveedor(datos)
      notificar(editando !== null ? 'Proveedor actualizado.' : 'Proveedor creado.', 'ok')
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
      await actualizarProveedor(aCambiarEstado.id, { activo: !aCambiarEstado.activo })
      notificar(aCambiarEstado.activo ? 'Proveedor desactivado.' : 'Proveedor reactivado.', 'ok')
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
          <h1>Proveedores</h1>
          <p className="page-sub">Guarda precios y condiciones de entrega de tus proveedores.</p>
        </div>
        <div className="page-actions">
          <button type="button" className="btn btn-primary" onClick={abrirCrear}>
            Nuevo proveedor
          </button>
        </div>
      </div>

      <div className="toolbar">
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
            {[0, 1, 2].map((indice) => (
              <div key={indice} className="skeleton skeleton-row" />
            ))}
          </div>
        )}

        {!cargando && error !== null && (
          <div className="empty">
            <span className="empty-icon" aria-hidden="true">!</span>
            <h3>No se pudieron cargar los proveedores</h3>
            <p>{error}</p>
            <button type="button" className="btn btn-ghost" onClick={() => void recargar()}>
              Reintentar
            </button>
          </div>
        )}

        {!cargando && error === null && proveedores.length === 0 && (
          <div className="empty tabla-vacia">
            <span className="empty-icon" aria-hidden="true">＋</span>
            <h3>Aún no hay proveedores</h3>
            <p>Registra a quién le compras para tener sus datos a mano.</p>
          </div>
        )}

        {!cargando && error === null && proveedores.length > 0 && (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Proveedor</th>
                  <th scope="col">Contacto</th>
                  <th scope="col">Precio habitual</th>
                  <th scope="col">Estado</th>
                  <th scope="col" style={{ textAlign: 'right' }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {proveedores.map((proveedor) => (
                  <tr key={proveedor.id}>
                    <td data-label="Proveedor" className="cell-strong">{proveedor.nombre}</td>
                    <td data-label="Contacto" className="cell-muted">
                      {proveedor.telefono ?? proveedor.contacto ?? '—'}
                    </td>
                    <td data-label="Precio habitual" className="num">
                      {proveedor.precio_habitual === null ? '—' : formatQ(proveedor.precio_habitual)}
                    </td>
                    <td data-label="Estado">
                      <span className={`pill ${proveedor.activo ? 'pill-good' : 'pill-neutral'}`}>
                        {proveedor.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td data-label="Acciones">
                      <div className="row-actions">
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => abrirEditar(proveedor)}
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => setACambiarEstado(proveedor)}
                        >
                          {proveedor.activo ? 'Desactivar' : 'Reactivar'}
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
        titulo={editando !== null ? 'Editar proveedor' : 'Nuevo proveedor'}
        onCerrar={() => setDialogoAbierto(false)}
        pie={
          <>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => setDialogoAbierto(false)}
              disabled={guardando}
            >
              Cancelar
            </button>
            <button type="submit" form="form-proveedor" className="btn btn-primary" disabled={guardando}>
              {guardando ? 'Guardando…' : 'Guardar'}
            </button>
          </>
        }
      >
        <form id="form-proveedor" className="form-grid" onSubmit={guardar}>
          <div className="field span-2">
            <label className="field-label" htmlFor="proveedor-nombre">Nombre</label>
            <input
              id="proveedor-nombre"
              className="input"
              value={formulario.nombre}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, nombre: evento.target.value }))
              }
              placeholder="Ej. Distribuidora Bella"
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="proveedor-contacto">Persona de contacto</label>
            <input
              id="proveedor-contacto"
              className="input"
              value={formulario.contacto}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, contacto: evento.target.value }))
              }
              placeholder="Opcional"
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="proveedor-telefono">Teléfono</label>
            <input
              id="proveedor-telefono"
              className="input"
              value={formulario.telefono}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, telefono: evento.target.value }))
              }
              placeholder="Opcional"
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="proveedor-email">Correo</label>
            <input
              id="proveedor-email"
              className="input"
              type="email"
              value={formulario.email}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, email: evento.target.value }))
              }
              placeholder="Opcional"
            />
          </div>
          <div className="field">
            <label className="field-label" htmlFor="proveedor-precio">Precio habitual (Q)</label>
            <input
              id="proveedor-precio"
              className="input"
              inputMode="decimal"
              value={formulario.precioHabitual}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, precioHabitual: evento.target.value }))
              }
              placeholder="Opcional"
            />
          </div>
          <div className="field span-2">
            <label className="field-label" htmlFor="proveedor-condiciones">Condiciones de entrega</label>
            <textarea
              id="proveedor-condiciones"
              className="textarea"
              value={formulario.condicionesEntrega}
              onChange={(evento) =>
                setFormulario((actual) => ({ ...actual, condicionesEntrega: evento.target.value }))
              }
              placeholder="Opcional"
            />
          </div>
        </form>
      </Dialogo>

      <DialogoConfirmacion
        abierto={aCambiarEstado !== null}
        titulo={aCambiarEstado?.activo === true ? 'Desactivar proveedor' : 'Reactivar proveedor'}
        mensaje={
          aCambiarEstado?.activo === true
            ? 'El proveedor dejará de aparecer al registrar productos nuevos. Podrás reactivarlo después.'
            : 'El proveedor volverá a estar disponible para asociarlo a productos.'
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
