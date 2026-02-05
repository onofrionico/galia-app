import { NavLink } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { 
  LayoutDashboard, 
  Calendar, 
  ShoppingCart, 
  Receipt, 
  BarChart3, 
  Users 
} from 'lucide-react'

const Sidebar = () => {
  const { isAdmin } = useAuth()

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', adminOnly: false },
    { to: '/schedules', icon: Calendar, label: 'Horarios', adminOnly: false },
    { to: '/sales', icon: ShoppingCart, label: 'Ventas', adminOnly: false },
    { to: '/expenses', icon: Receipt, label: 'Gastos', adminOnly: true },
    { to: '/reports', icon: BarChart3, label: 'Reportes', adminOnly: true },
    { to: '/employees', icon: Users, label: 'Empleados', adminOnly: true },
  ]

  const filteredNavItems = navItems.filter(item => !item.adminOnly || isAdmin())

  return (
    <aside className="w-64 bg-white border-r min-h-[calc(100vh-73px)]">
      <nav className="p-4 space-y-2">
        {filteredNavItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-gray-700 hover:bg-gray-100'
                }`
              }
            >
              <Icon className="h-5 w-5" />
              <span className="font-medium">{item.label}</span>
            </NavLink>
          )
        })}
      </nav>
    </aside>
  )
}

export default Sidebar
