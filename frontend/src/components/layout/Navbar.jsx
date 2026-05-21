import { useAuth } from '@/context/AuthContext'
import { LogOut, User, Menu } from 'lucide-react'
import NotificationBell from '../notifications/NotificationBell'
import { useState, useEffect } from 'react'
import { configService } from '@/services/configService'
import { useNavigate } from 'react-router-dom'

const Navbar = ({ onMenuClick }) => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [logoPath, setLogoPath] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchBrandingConfig = async () => {
      try {
        const config = await configService.getBrandingConfig()
        setLogoPath(config.logo_path)
      } catch (error) {
        console.error('Error loading logo:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchBrandingConfig()
  }, [])

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Error al cerrar sesión:', error)
    }
  }

  const handleLogoClick = () => {
    navigate('/dashboard')
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

            {/* Logo or Fallback Text */}
            <button
              onClick={handleLogoClick}
              className="flex items-center hover:opacity-80 transition-opacity"
            >
              {logoPath && !loading ? (
                <img
                  src={logoPath}
                  alt="Galia Logo"
                  className="h-12 md:h-16 object-contain"
                />
              ) : (
                <h1 className="text-xl md:text-2xl font-bold text-primary">Galia</h1>
              )}
            </button>

            <span className="hidden sm:inline text-xs md:text-sm text-muted-foreground">Gestión de Cafetería</span>
          </div>
          
          <div className="flex items-center space-x-2 md:space-x-4">
            <NotificationBell />
            
            <div className="hidden sm:flex items-center space-x-2">
              <User className="h-4 md:h-5 w-4 md:w-5 text-muted-foreground" />
              <span className="text-xs md:text-sm font-medium truncate max-w-[120px] md:max-w-none">{user?.email}</span>
              {user?.role === 'admin' && (
                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-primary/10 text-primary">
                  Admin
                </span>
              )}
            </div>
            
            <button
              onClick={handleLogout}
              className="flex items-center space-x-1 md:space-x-2 px-2 md:px-4 py-2 text-xs md:text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
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
