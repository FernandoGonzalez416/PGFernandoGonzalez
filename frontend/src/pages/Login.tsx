import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router'
import { useAuth } from '../auth/useAuth'
import { DATOS_FICTICIOS } from '../lib/env'
import { mensajeDeError } from '../lib/errores'

export function Login() {
  const { perfil, cargando, iniciarSesion } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  if (perfil !== null) return <Navigate to="/productos" replace />

  const enviar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    setError(null)
    if (email.trim() === '' || password === '') {
      setError('Ingresa tu correo y tu contraseña.')
      return
    }
    setEnviando(true)
    try {
      await iniciarSesion(email.trim(), password)
    } catch (fallo) {
      setError(mensajeDeError(fallo))
    } finally {
      setEnviando(false)
    }
  }

  const ocupado = enviando || cargando

  return (
    <div className="login-wrap">
      <section className="login-aside">
        <div className="login-ornament" aria-hidden="true" />
        <div className="login-aside-inner">
          <div className="login-brand">
            <span className="brand-mark" aria-hidden="true">FC</span>
            <strong>Familia de la Cruz</strong>
          </div>
          <h2>Tu inventario, siempre bajo control.</h2>
          <p>
            Registra productos, controla existencias y mantén tu catálogo al día desde un solo
            lugar, pensado para el día a día del negocio.
          </p>
        </div>
      </section>

      <section className="login-main">
        <div className="login-inner">
          <div>
            <h1 className="login-title">Iniciar sesión</h1>
            <p className="login-sub">Accede con tu cuenta para administrar el catálogo.</p>
          </div>

          <form className="login-form" onSubmit={enviar}>
            {error !== null && <div className="login-error" role="alert">{error}</div>}

            <div className="field">
              <label className="field-label" htmlFor="email">Correo electrónico</label>
              <input
                id="email"
                className="input"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(evento) => setEmail(evento.target.value)}
                placeholder="tu@correo.com"
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="password">Contraseña</label>
              <input
                id="password"
                className="input"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(evento) => setPassword(evento.target.value)}
                placeholder="••••••••"
              />
            </div>

            <button type="submit" className="btn btn-primary btn-block" disabled={ocupado}>
              {ocupado ? 'Ingresando…' : 'Ingresar'}
            </button>
          </form>

          {DATOS_FICTICIOS && (
            <div className="login-demo">
              <strong>Cuentas de prueba</strong>
              <br />
              propietario@prueba.com · padre@prueba.com
              <br />
              Contraseña: 123456
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
