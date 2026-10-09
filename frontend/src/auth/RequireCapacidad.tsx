import type { ReactNode } from 'react'
import type { Capacidad } from '../api/types'
import { NoAutorizado } from '../pages/NoAutorizado'
import { useCan } from './useCan'

export function RequireCapacidad({
  capacidad,
  children,
}: {
  capacidad: Capacidad
  children: ReactNode
}) {
  const puede = useCan(capacidad)
  if (!puede) return <NoAutorizado />
  return <>{children}</>
}
