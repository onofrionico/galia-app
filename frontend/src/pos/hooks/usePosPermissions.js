import { useMemo } from 'react'
import { useAuth } from '@/context/AuthContext'
import { posPermissions } from '../utils/permissions'

export function usePosPermissions() {
  const { isAdmin, userModules } = useAuth()
  const admin = isAdmin()
  return useMemo(
    () => posPermissions({ isAdmin: admin, modules: userModules.map((m) => m.name) }),
    [admin, userModules],
  )
}
