import { Link } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { usePosPermissions } from '../hooks/usePosPermissions'
import CenteredMessage from '../ui/CenteredMessage'

// require: 'canUse' (POS o Camarero) o 'pos' (solo caja).
export default function PosRoute({ require = 'canUse', children }) {
  const { loading } = useAuth()
  const perms = usePosPermissions()
  if (loading) return null
  if (!perms[require]) {
    return (
      <CenteredMessage>
        <div>
          <p className="text-lg font-semibold text-galia-plum">No tenés acceso a esta parte del POS.</p>
          <Link to="/dashboard" className="mt-2 inline-block underline">Volver a Galia</Link>
        </div>
      </CenteredMessage>
    )
  }
  return children
}
