import { NavLink } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { X } from 'lucide-react'
import { 
  LayoutDashboard, 
  Calendar, 
  Clock,
  LogIn,
  ShoppingCart, 
  Receipt, 
  BarChart3, 
  Users,
  Briefcase,
  Brain
} from 'lucide-react'

const Sidebar = ({ isOpen, onClose }) => {
  const { isAdmin } = useAuth()

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', adminOnly: false },
    { to: '/my-schedule', icon: Clock, label: 'Mi Horario', adminOnly: false, employeeOnly: true },
    { to: '/time-tracking', icon: LogIn, label: 'Carga de Horarios', adminOnly: false, employeeOnly: true },
    { to: '/schedules', icon: Calendar, label: 'Horarios', adminOnly: true },
    { to: '/sales', icon: ShoppingCart, label: 'Ventas', adminOnly: true },
    { to: '/expenses', icon: Receipt, label: 'Gastos', adminOnly: true },
    { to: '/reports', icon: BarChart3, label: 'Reportes', adminOnly: true },
    { to: '/employees', icon: Users, label: 'Empleados', adminOnly: true },
    { to: '/job-positions', icon: Briefcase, label: 'Puestos', adminOnly: true },
    { to: '/ml-dashboard', icon: Brain, label: 'Dashboard ML', adminOnly: true },
  ]

  const filteredNavItems = navItems.filter(item => {
    if (item.adminOnly && !isAdmin()) return false
    if (item.employeeOnly && isAdmin()) return false
    return true
  })

  return (
    <>
      <aside className={`fixed md:static top-0 left-0 z-40 w-64 bg-white border-r min-h-screen transition-transform duration-300 transform ${
        isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      }`}>
        <nav className="p-4 space-y-2 md:mt-0 mt-16">
          <button
            onClick={onClose}
            className="md:hidden absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="h-6 w-6 text-gray-600" />
          </button>
          
          {filteredNavItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`
                }
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                <span className="font-medium">{item.label}</span>
              </NavLink>
            )
          })}
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
