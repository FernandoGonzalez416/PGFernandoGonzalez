function leerVariable(valor: string | undefined, porDefecto: string): string {
  return valor !== undefined && valor.trim() !== '' ? valor : porDefecto
}

export const API_URL = leerVariable(import.meta.env.VITE_API_URL, 'http://127.0.0.1:8000')
export const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL ?? ''
export const SUPABASE_PUBLISHABLE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? ''
export const DATOS_FICTICIOS = import.meta.env.VITE_DATOS_FICTICIOS === 'true'
export const APP_NAME = leerVariable(import.meta.env.VITE_APP_NAME, 'Familia de la Cruz')
