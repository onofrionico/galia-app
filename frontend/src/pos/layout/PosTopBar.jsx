import { Link, NavLink, useMatch } from 'react-router-dom'
import { LogOut, Settings } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { useFloor } from '../hooks/usePosQueries'
import { usePosPermissions } from '../hooks/usePosPermissions'
import CashStatusBadge from '../cash/CashStatusBadge'
import PrintStatusBadge from '../print/PrintStatusBadge'

const tabClass = ({ isActive }) =>
  `flex min-h-[44px] items-center whitespace-nowrap rounded-lg px-4 font-medium ${
    isActive ? 'bg-galia-cream text-galia-plum' : 'text-galia-cream/80 hover:bg-white/10'
  }`

export default function PosTopBar() {
  const match = useMatch('/pos/salon/:salonId')
  const salonId = match ? Number(match.params.salonId) : undefined
  // Misma clave que el plano del salón abierto: React Query no repite el pedido.
  const { data } = useFloor(salonId)
  const perms = usePosPermissions()
  const { user } = useAuth()

  return (
    <header className="flex items-center gap-2 bg-galia-plum px-3 py-2 text-galia-cream">
      <span className="mr-2 font-display text-xl tracking-wide">GALIA POS</span>
      <nav className="flex min-w-0 flex-1 gap-1 overflow-x-auto" aria-label="Salones">
        {(data?.salons ?? []).map((salon) => (
          <NavLink key={salon.id} to={`/pos/salon/${salon.id}`} className={tabClass}>{salon.name}</NavLink>
        ))}
        {perms.pos && <NavLink to="/pos/mostrador" className={tabClass}>Mostrador</NavLink>}
        {perms.pos && <NavLink to="/pos/caja" className={tabClass}>Caja</NavLink>}
      </nav>
      {perms.pos && (
        <NavLink to="/pos/config" className={tabClass} aria-label="Configuración del POS">
          <Settings size={18} />
        </NavLink>
      )}
      <CashStatusBadge />
      {perms.pos && <PrintStatusBadge />}
      <span className="hidden px-2 text-sm text-galia-cream/80 md:block">{user?.email}</span>
      <Link to="/dashboard" className="flex min-h-[44px] items-center gap-2 rounded-lg px-3 text-sm hover:bg-white/10">
        <LogOut size={16} /> Salir a Galia
      </Link>
    </header>
  )
}
