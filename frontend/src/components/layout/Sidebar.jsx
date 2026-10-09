import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { ChevronDown, X, LayoutDashboard, User } from 'lucide-react'
import {
  Calendar,
  Clock,
  Upload,
  FileText,
  Users,
  Briefcase,
  CalendarDays,
  ShoppingCart,
  Receipt,
  Tag,
  Wallet,
  AlertTriangle,
  BarChart3,
  Brain,
  DollarSign,
  LogIn,
  BookOpen,
  Inbox,
} from 'lucide-react'

const alwaysVisibleAdmin = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/profile', icon: User, label: 'Mi Perfil' },
]

const alwaysVisibleEmployee = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/my-schedule', icon: Clock, label: 'Mi Horario' },
  { to: '/time-tracking', icon: LogIn, label: 'Carga de Horarios' },
  { to: '/my-payrolls', icon: Wallet, label: 'Mis Nóminas' },
  { to: '/my-documents', icon: FileText, label: 'Mis Recibos' },
  { to: '/my-absence-requests', icon: FileText, label: 'Mis Ausencias' },
  { to: '/profile', icon: User, label: 'Mi Perfil' },
]

const navGroups = [
  {
    id: 'personal',
    label: 'Personal',
    icon: Users,
    accentText: 'text-galia-coral',
    accentBorder: 'border-galia-coral',
    items: [
      { to: '/schedules', icon: Calendar, label: 'Horarios' },
      { to: '/admin-time-tracking', icon: Clock, label: 'Gestión de Horas' },
      { to: '/import-time-tracking', icon: Upload, label: 'Importar Horas', subItem: true },
      { to: '/absence-requests', icon: FileText, label: 'Solicitudes de Ausencia' },
      { to: '/employees', icon: Users, label: 'Empleados' },
      { to: '/job-positions', icon: Briefcase, label: 'Puestos' },
      { to: '/holidays', icon: CalendarDays, label: 'Feriados' },
    ],
  },
  {
    id: 'finanzas',
    label: 'Finanzas',
    icon: DollarSign,
    accentText: 'text-galia-lime',
    accentBorder: 'border-galia-lime',
    items: [
      { to: '/sales', icon: ShoppingCart, label: 'Ventas' },
      { to: '/expenses', icon: Receipt, label: 'Gastos' },
      { to: '/expense-categories', icon: Tag, label: 'Categorías de Gastos', subItem: true },
      { to: '/payroll', icon: Wallet, label: 'Sueldos' },
      { to: '/payroll-claims', icon: AlertTriangle, label: 'Reclamos de Nóminas', subItem: true },
    ],
  },
  {
    id: 'analisis',
    label: 'Análisis',
    icon: BarChart3,
    accentText: 'text-galia-cream',
    accentBorder: 'border-galia-cream',
    items: [
      { to: '/reports', icon: BarChart3, label: 'Reportes' },
      { to: '/ml-dashboard', icon: Brain, label: 'Dashboard ML' },
    ],
  },
  {
    id: 'carta',
    label: 'Carta',
    icon: BookOpen,
    accentText: 'text-blue-200',
    accentBorder: 'border-blue-200',
    items: [
      { to: '/menu', icon: BookOpen, label: 'Carta' },
      { to: '/menu/inbox', icon: Inbox, label: 'Nuevos y alertas', subItem: true },
    ],
  },
]

const getActiveGroup = (pathname) =>
  navGroups.find(g => g.items.some(i => pathname.startsWith(i.to)))?.id ?? null

const ActiveFlower = () => (
  <img src="/brand/flower-lime.png" alt="" aria-hidden="true" className="h-3.5 w-3.5 flex-shrink-0" />
)

const Sidebar = ({ isOpen, onClose }) => {
  const { isAdmin } = useAuth()
  const location = useLocation()

  const [openGroup, setOpenGroup] = useState(() => {
    const fromRoute = getActiveGroup(location.pathname)
    if (fromRoute) return fromRoute
    return localStorage.getItem('sidebar_open_group') ?? null
  })

  useEffect(() => {
    const fromRoute = getActiveGroup(location.pathname)
    if (fromRoute) {
      setOpenGroup(fromRoute)
      localStorage.setItem('sidebar_open_group', fromRoute)
    }
  }, [location.pathname])

  const handleGroupClick = (groupId) => {
    const next = openGroup === groupId ? null : groupId
    setOpenGroup(next)
    if (next) {
      localStorage.setItem('sidebar_open_group', next)
    } else {
      localStorage.removeItem('sidebar_open_group')
    }
  }

  const renderNavLink = (item, extraClass = '') => {
    const Icon = item.icon
    return (
      <NavLink
        key={item.to}
        to={item.to}
        onClick={onClose}
        className={({ isActive }) =>
          `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
            isActive
              ? 'bg-white/10 text-white'
              : 'text-galia-cream/70 hover:bg-white/5 hover:text-galia-cream'
          } ${extraClass}`
        }
      >
        {({ isActive }) => (
          <>
            <Icon className="h-4 w-4 flex-shrink-0" />
            <span className="font-medium flex-1">{item.label}</span>
            {isActive && <ActiveFlower />}
          </>
        )}
      </NavLink>
    )
  }

  return (
    <>
      <aside className={`fixed md:static top-0 left-0 z-40 w-64 bg-galia-plum-dark text-galia-cream border-r border-white/10 min-h-screen transition-transform duration-300 transform ${
        isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      }`}>
        <nav className="p-4 space-y-1">
          <button
            onClick={onClose}
            aria-label="Cerrar menú"
            className="md:hidden absolute top-4 right-4 p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="h-6 w-6 text-galia-cream" />
          </button>

          <div className="flex justify-center pb-4 mb-2 border-b border-white/10">
            <div className="bg-galia-cream rounded-2xl p-2">
              <img src="/brand/logo.png" alt="Galia Café" className="h-14 w-auto" />
            </div>
          </div>

          {isAdmin() ? (
            <>
              {alwaysVisibleAdmin.map(item => renderNavLink(item))}

              <div className="pt-2 space-y-1">
                {navGroups.map(group => {
                  const GroupIcon = group.icon
                  const isGroupOpen = openGroup === group.id
                  const isGroupActive = getActiveGroup(location.pathname) === group.id

                  return (
                    <div
                      key={group.id}
                      className={`rounded-lg border-l-2 overflow-hidden transition-colors ${
                        isGroupActive ? group.accentBorder : 'border-transparent'
                      }`}
                    >
                      <button
                        onClick={() => handleGroupClick(group.id)}
                        className={`w-full flex items-center justify-between px-4 py-2.5 text-sm font-semibold transition-colors ${
                          isGroupActive ? `${group.accentText} bg-white/5` : 'text-galia-cream/70 hover:bg-white/5'
                        }`}
                      >
                        <span className="flex items-center gap-3">
                          <GroupIcon className={`h-4 w-4 flex-shrink-0 ${group.accentText}`} />
                          {group.label}
                        </span>
                        <ChevronDown
                          className={`h-4 w-4 transition-transform duration-200 ${
                            isGroupOpen ? 'rotate-180' : ''
                          }`}
                        />
                      </button>

                      <div
                        className={`overflow-hidden transition-all duration-200 ease-in-out ${
                          isGroupOpen ? 'max-h-96' : 'max-h-0'
                        }`}
                      >
                        <div className="pb-2 pt-1 px-2 space-y-0.5">
                          {group.items.map(item => {
                            const Icon = item.icon
                            return (
                              <NavLink
                                key={item.to}
                                to={item.to}
                                onClick={onClose}
                                className={({ isActive }) =>
                                  `flex items-center gap-3 rounded-md transition-colors ${
                                    item.subItem
                                      ? 'pl-7 pr-3 py-2 text-xs'
                                      : 'px-3 py-2 text-sm'
                                  } ${
                                    isActive
                                      ? 'bg-white/10 text-white font-medium'
                                      : 'text-galia-cream/70 hover:bg-white/5 hover:text-galia-cream'
                                  }`
                                }
                              >
                                {({ isActive }) => (
                                  <>
                                    <Icon className="h-3.5 w-3.5 flex-shrink-0" />
                                    <span className={`flex-1 ${item.subItem ? '' : 'font-medium'}`}>
                                      {item.label}
                                    </span>
                                    {isActive && <ActiveFlower />}
                                  </>
                                )}
                              </NavLink>
                            )
                          })}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          ) : (
            alwaysVisibleEmployee.map(item => renderNavLink(item))
          )}
        </nav>
      </aside>

      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
          onClick={onClose}
        />
      )}
    </>
  )
}

export default Sidebar
