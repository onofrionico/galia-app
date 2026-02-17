import { createContext, useContext, useState, useEffect } from 'react'

const ThemeContext = createContext()

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState({
    primary_color: '#3B82F6',
    secondary_color: '#10B981',
    accent_color: '#F59E0B',
    cafeteria_name: 'Galia',
    logo_url: null
  })

  useEffect(() => {
    fetchTheme()

    const handleSettingsUpdate = (event) => {
      setTheme(event.detail)
      applyTheme(event.detail)
    }

    window.addEventListener('settingsUpdated', handleSettingsUpdate)

    return () => {
      window.removeEventListener('settingsUpdated', handleSettingsUpdate)
    }
  }, [])

  const fetchTheme = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) return

      const response = await fetch('http://localhost:5001/api/settings', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setTheme(data)
        applyTheme(data)
      }
    } catch (error) {
      // Silently fail if backend is not running - use default theme
      console.warn('No se pudo cargar el tema personalizado, usando valores por defecto')
    }
  }

  const applyTheme = (themeData) => {
    document.documentElement.style.setProperty('--color-primary', themeData.primary_color)
    document.documentElement.style.setProperty('--color-secondary', themeData.secondary_color)
    document.documentElement.style.setProperty('--color-accent', themeData.accent_color)
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, fetchTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
