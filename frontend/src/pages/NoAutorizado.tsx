import { Link } from 'react-router'

export function NoAutorizado() {
  return (
    <div className="forbidden">
      <span className="forbidden-code">403</span>
      <h2>No tienes acceso a esta sección</h2>
      <p>
        Tu usuario no cuenta con los permisos necesarios para ver esta pantalla. Si crees que es
        un error, contacta al administrador.
      </p>
      <Link to="/productos" className="btn btn-ghost">
        Volver a productos
      </Link>
    </div>
  )
}
