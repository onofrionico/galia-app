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
    activeClass: 'text-green-700 bg-green-50 border-green-200',
    headerClass: 'text-green-700 bg-green-50',
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
    activeClass: 'text-blue-700 bg-blue-50 border-blue-200',
    headerClass: 'text-blue-700 bg-blue-50',
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
    activeClass: 'text-purple-700 bg-purple-50 border-purple-200',
    headerClass: 'text-purple-700 bg-purple-50',
    items: [
      { to: '/reports', icon: BarChart3, label: 'Reportes' },
      { to: '/ml-dashboard', icon: Brain, label: 'Dashboard ML' },
    ],
  },
]

const getActiveGroup = (pathname) =>
  navGroups.find(g => g.items.some(i => pathname.startsWith(i.to)))?.id ?? null

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
              ? 'bg-primary text-primary-foreground'
              : 'text-gray-700 hover:bg-gray-100'
          } ${extraClass}`
        }
      >
        <Icon className="h-4 w-4 flex-shrink-0" />
        <span className="font-medium">{item.label}</span>
      </NavLink>
    )
  }

  return (
    <>
      <aside className={`fixed md:static top-0 left-0 z-40 w-64 bg-white border-r min-h-screen transition-transform duration-300 transform ${
        isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      }`}>
        <nav className="p-4 space-y-1 md:mt-0 mt-16">
          <button
            onClick={onClose}
            className="md:hidden absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-6 w-6 text-gray-600" />
          </button>

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
                      className={`rounded-lg border overflow-hidden transition-colors ${
                        isGroupActive ? group.activeClass : 'border-gray-200'
                      }`}
                    >
                      <button
                        onClick={() => handleGroupClick(group.id)}
                        className={`w-full flex items-center justify-between px-4 py-2.5 text-sm font-semibold transition-colors ${
                          isGroupActive ? group.headerClass : 'text-gray-600 hover:bg-gray-50'
                        }`}
                      >
                        <span className="flex items-center gap-3">
                          <GroupIcon className="h-4 w-4 flex-shrink-0" />
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
                                      ? 'bg-primary text-primary-foreground font-medium'
                                      : 'text-gray-600 hover:bg-gray-100'
                                  }`
                                }
                              >
                                <Icon className="h-3.5 w-3.5 flex-shrink-0" />
                                <span className={item.subItem ? '' : 'font-medium'}>
                                  {item.label}
                                </span>
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
