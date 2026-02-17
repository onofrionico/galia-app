import { useAuth } from '@/context/AuthContext'
import { useTheme } from '@/context/ThemeContext'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, User, Menu, Settings, UserCircle } from 'lucide-react'
import NotificationBell from '../notifications/NotificationBell'

const Navbar = ({ onMenuClick }) => {
  const { user, logout } = useAuth()
  const { theme } = useTheme()
  const navigate = useNavigate()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Error al cerrar sesión:', error)
    }
  }

  const handleProfileClick = () => {
    setShowUserMenu(false)
    navigate('/profile')
  }

  return (
    <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="px-4 md:px-6 py-3 md:py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 md:space-x-4">
            <button
              onClick={onMenuClick}
              className="md:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Menu className="h-6 w-6 text-gray-600" />
            </button>
            {theme?.logo_url ? (
              <img 
                src={`http://localhost:5001${theme.logo_url}`} 
                alt={theme.cafeteria_name || 'Galia'}
                className="h-8 md:h-10 w-auto object-contain"
              />
            ) : (
              <h1 className="text-xl md:text-2xl font-bold text-primary">{theme?.cafeteria_name || 'Galia'}</h1>
            )}
            <span className="hidden sm:inline text-xs md:text-sm text-muted-foreground">Gestión de Cafetería</span>
          </div>
          
          <div className="flex items-center space-x-2 md:space-x-4">
            <NotificationBell />
            
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="hidden sm:flex items-center space-x-2 px-3 py-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <User className="h-4 md:h-5 w-4 md:w-5 text-muted-foreground" />
                <span className="text-xs md:text-sm font-medium truncate max-w-[120px] md:max-w-none">{user?.email}</span>
                {user?.role === 'admin' && (
                  <span className="px-2 py-1 text-xs font-semibold rounded-full bg-primary/10 text-primary">
                    Admin
                  </span>
                )}
              </button>

              {showUserMenu && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowUserMenu(false)}
                  />
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border z-20">
                    <div className="py-1">
                      <button
                        onClick={handleProfileClick}
                        className="w-full flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                      >
                        <UserCircle className="h-4 w-4" />
                        <span>Mi Perfil</span>
                      </button>
                      {user?.role === 'admin' && (
                        <button
                          onClick={() => {
                            setShowUserMenu(false)
                            navigate('/settings')
                          }}
                          className="w-full flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                        >
                          <Settings className="h-4 w-4" />
                          <span>Ajustes</span>
                        </button>
                      )}
                      <div className="border-t my-1"></div>
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center space-x-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>Cerrar Sesión</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
            
            <button
              onClick={handleLogout}
              className="sm:hidden flex items-center space-x-1 md:space-x-2 px-2 md:px-4 py-2 text-xs md:text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Salir</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
