import type { ReactNode } from 'react'

type Tono = 'ok' | 'amber' | 'red' | 'neutral' | 'nude'

const CLASES: Record<Tono, string> = {
  ok: 'pill pill-good',
  amber: 'pill pill-amber',
  red: 'pill pill-red',
  neutral: 'pill pill-neutral',
  nude: 'pill pill-nude',
}

/** Etiqueta de estado con colores semánticos (ámbar/rojo/verde solo para estado, nunca decoración). */
export function Badge({ tono = 'neutral', children }: { tono?: Tono; children: ReactNode }) {
  return <span className={CLASES[tono]}>{children}</span>
}
