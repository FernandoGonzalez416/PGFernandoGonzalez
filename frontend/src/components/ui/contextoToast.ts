import { createContext } from 'react'

export type NivelToast = 'ok' | 'error' | 'info'
export type Notificar = (mensaje: string, nivel?: NivelToast) => void

export type ContextoToastValor = { notificar: Notificar; exito: (mensaje: string) => void; error: (mensaje: string) => void; info: (mensaje: string) => void }

export const ContextoToast = createContext<ContextoToastValor | null>(null)
