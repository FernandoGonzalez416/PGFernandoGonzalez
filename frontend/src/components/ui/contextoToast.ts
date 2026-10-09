import { createContext } from 'react'

export type NivelToast = 'ok' | 'error' | 'info'
export type Notificar = (mensaje: string, nivel?: NivelToast) => void

export type ContextoToastValor = { notificar: Notificar }

export const ContextoToast = createContext<ContextoToastValor | null>(null)
