import { Link } from 'react-router'

export function NoEncontrado() {
  return (
    <div className="forbidden">
      <span className="forbidden-code">404</span>
      <h2>No encontramos esta página</h2>
      <p>La dirección a la que intentas acceder no existe o fue movida.</p>
      <Link to="/productos" className="btn btn-ghost">
        Ir a productos
      </Link>
    </div>
  )
}
