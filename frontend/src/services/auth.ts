import type { AuthChangeEvent, Session } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'

export async function iniciarSesion(email: string, password: string): Promise<void> {
  const { error } = await supabase.auth.signInWithPassword({ email, password })
  if (error) throw new Error('Correo o contraseña incorrectos.')
}

export async function cerrarSesion(): Promise<void> {
  await supabase.auth.signOut()
}

export async function obtenerSesionActual(): Promise<Session | null> {
  const { data } = await supabase.auth.getSession()
  return data.session
}

export async function obtenerAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? null
}

export function alCambiarSesion(
  callback: (evento: AuthChangeEvent, sesion: Session | null) => void,
): () => void {
  const { data } = supabase.auth.onAuthStateChange((evento, sesion) => {
    callback(evento, sesion)
  })
  return () => {
    data.subscription.unsubscribe()
  }
}
