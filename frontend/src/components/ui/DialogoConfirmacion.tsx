import { Dialogo } from './Dialogo'

export function DialogoConfirmacion({
  abierto,
  titulo,
  mensaje,
  textoConfirmar = 'Confirmar',
  peligroso = false,
  ocupado = false,
  onConfirmar,
  onCerrar,
}: {
  abierto: boolean
  titulo: string
  mensaje: string
  textoConfirmar?: string
  peligroso?: boolean
  ocupado?: boolean
  onConfirmar: () => void
  onCerrar: () => void
}) {
  return (
    <Dialogo
      abierto={abierto}
      titulo={titulo}
      onCerrar={onCerrar}
      pie={
        <>
          <button type="button" className="btn btn-ghost" onClick={onCerrar} disabled={ocupado}>
            Cancelar
          </button>
          <button
            type="button"
            className={`btn ${peligroso ? 'btn-nude' : 'btn-primary'}`}
            onClick={onConfirmar}
            disabled={ocupado}
          >
            {ocupado ? 'Procesando…' : textoConfirmar}
          </button>
        </>
      }
    >
      <p>{mensaje}</p>
    </Dialogo>
  )
}
