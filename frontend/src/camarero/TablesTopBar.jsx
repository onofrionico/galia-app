import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LayoutGrid, Map as MapIcon, Menu } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'

const pill = (active) =>
  `min-h-[48px] whitespace-nowrap rounded-full px-4 text-sm font-medium ${
    active ? 'bg-galia-cream text-galia-plum' : 'bg-white/10 text-galia-cream'
  }`

const VIEWS = [['list', 'Lista', LayoutGrid], ['floor', 'Plano', MapIcon]]
const FILTERS = [['all', 'Todas'], ['mine', 'Mías']]

export default function TablesTopBar({ salons, salonId, onSalon, view, onView, filter, onFilter }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  const signOut = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="bg-galia-plum pt-[env(safe-area-inset-top)] text-galia-cream">
      <div className="flex items-center gap-2 px-3 py-2">
        <span className="font-display text-lg tracking-wide">CAMARERO</span>
        <div className="ml-auto flex gap-1" role="group" aria-label="Vista">
          {VIEWS.map(([value, label, Icon]) => (
            <button key={value} type="button" aria-pressed={view === value} onClick={() => onView(value)}
              className={`${pill(view === value)} flex items-center gap-1`}>
              <Icon size={16} /> {label}
            </button>
          ))}
        </div>
        <button type="button" aria-label="Menú" aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}
          className="flex min-h-[48px] min-w-[48px] items-center justify-center rounded-lg hover:bg-white/10">
          <Menu size={22} />
        </button>
      </div>
      {menuOpen && (
        <div className="border-t border-white/10 px-3 py-2 text-sm">
          <p className="py-2 text-galia-cream/80">{user?.email}</p>
          <Link to="/dashboard" className="flex min-h-[48px] items-center">Salir a Galia</Link>
          <button type="button" onClick={signOut} className="flex min-h-[48px] w-full items-center text-left">Cerrar sesión</button>
        </div>
      )}
      <nav className="flex gap-2 overflow-x-auto px-3 pb-2" aria-label="Salones">
        {salons.map((salon) => (
          <button key={salon.id} type="button" aria-pressed={salon.id === salonId} onClick={() => onSalon(salon.id)}
            className={pill(salon.id === salonId)}>
            {salon.name}
          </button>
        ))}
      </nav>
      <div className="flex gap-2 px-3 pb-3" role="group" aria-label="Filtro de mesas">
        {FILTERS.map(([value, label]) => (
          <button key={value} type="button" aria-pressed={filter === value} onClick={() => onFilter(value)}
            className={pill(filter === value)}>
            {label}
          </button>
        ))}
      </div>
    </header>
  )
}
