import { Check, X } from 'lucide-react'
import { Button } from './Button'
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
          <Button
            variante="ghost"
            iconoIzquierdo={<X aria-hidden="true" />}
            onClick={onCerrar}
            disabled={ocupado}
          >
            Cancelar
          </Button>
          <Button
            variante={peligroso ? 'nude' : 'primary'}
            iconoIzquierdo={<Check aria-hidden="true" />}
            onClick={onConfirmar}
            cargando={ocupado}
          >
            {textoConfirmar}
          </Button>
        </>
      }
    >
      <p>{mensaje}</p>
    </Dialogo>
  )
}
