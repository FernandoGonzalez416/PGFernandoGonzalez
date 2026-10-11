import { useEffect, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'

export function Dialogo({
  abierto,
  titulo,
  onCerrar,
  children,
  pie,
}: {
  abierto: boolean
  titulo: string
  onCerrar: () => void
  children: ReactNode
  pie?: ReactNode
}) {
  const referencia = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialogo = referencia.current
    if (!dialogo) return
    if (abierto && !dialogo.open) dialogo.showModal()
    if (!abierto && dialogo.open) dialogo.close()
  }, [abierto])

  return (
    <dialog
      ref={referencia}
      className="dialog"
      aria-label={titulo}
      onCancel={(evento) => {
        evento.preventDefault()
        onCerrar()
      }}
      onClose={onCerrar}
    >
      <div className="dialog-head">
        <h2>{titulo}</h2>
        <button type="button" className="icon-btn" aria-label="Cerrar" onClick={onCerrar}>
          <X aria-hidden="true" />
        </button>
      </div>
      <div className="dialog-body">{children}</div>
      {pie !== undefined && <div className="dialog-foot">{pie}</div>}
    </dialog>
  )
}
