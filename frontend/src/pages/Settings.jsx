import { useState, useEffect } from 'react'
import { Save, Upload, X, Palette } from 'lucide-react'

const Settings = () => {
  const [settings, setSettings] = useState({
    primary_color: '#3B82F6',
    secondary_color: '#10B981',
    accent_color: '#F59E0B',
    cafeteria_name: 'Galia',
    logo_url: null
  })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [logoFile, setLogoFile] = useState(null)
  const [logoPreview, setLogoPreview] = useState(null)

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch('http://localhost:5001/api/settings', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setSettings(data)
        if (data.logo_url) {
          setLogoPreview(`http://localhost:5001${data.logo_url}`)
        }
      }
    } catch (error) {
      console.error('Error al cargar configuración:', error)
    }
  }

  const handleColorChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }))
  }

  const handleNameChange = (value) => {
    setSettings(prev => ({ ...prev, cafeteria_name: value }))
  }

  const handleLogoChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setLogoFile(file)
      const reader = new FileReader()
      reader.onloadend = () => {
        setLogoPreview(reader.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleSaveSettings = async () => {
    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const token = localStorage.getItem('auth_token')

      const response = await fetch('http://localhost:5001/api/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          primary_color: settings.primary_color,
          secondary_color: settings.secondary_color,
          accent_color: settings.accent_color,
          cafeteria_name: settings.cafeteria_name
        })
      })

      if (response.ok) {
        setMessage({ type: 'success', text: 'Configuración guardada exitosamente' })
        window.dispatchEvent(new CustomEvent('settingsUpdated', { detail: settings }))
      } else {
        setMessage({ type: 'error', text: 'Error al guardar configuración' })
      }
    } catch (error) {
      console.error('Error:', error)
      setMessage({ type: 'error', text: 'Error al guardar configuración' })
    } finally {
      setLoading(false)
    }
  }

  const handleUploadLogo = async () => {
    if (!logoFile) return

    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const token = localStorage.getItem('auth_token')
      const formData = new FormData()
      formData.append('logo', logoFile)

      const response = await fetch('http://localhost:5001/api/settings/logo', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        setSettings(prev => ({ ...prev, logo_url: data.logo_url }))
        setLogoPreview(`http://localhost:5001${data.logo_url}`)
        setLogoFile(null)
        setMessage({ type: 'success', text: 'Logo subido exitosamente' })
        window.dispatchEvent(new CustomEvent('settingsUpdated', { detail: { ...settings, logo_url: data.logo_url } }))
      } else {
        setMessage({ type: 'error', text: 'Error al subir logo' })
      }
    } catch (error) {
      console.error('Error:', error)
      setMessage({ type: 'error', text: 'Error al subir logo' })
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteLogo = async () => {
    setLoading(true)
    setMessage({ type: '', text: '' })

    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch('http://localhost:5001/api/settings/logo', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        setSettings(prev => ({ ...prev, logo_url: null }))
        setLogoPreview(null)
        setLogoFile(null)
        setMessage({ type: 'success', text: 'Logo eliminado exitosamente' })
        window.dispatchEvent(new CustomEvent('settingsUpdated', { detail: { ...settings, logo_url: null } }))
      } else {
        setMessage({ type: 'error', text: 'Error al eliminar logo' })
      }
    } catch (error) {
      console.error('Error:', error)
      setMessage({ type: 'error', text: 'Error al eliminar logo' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Ajustes de la Aplicación</h1>
        <p className="text-gray-600 mt-1">Personaliza los colores y el logo de tu cafetería</p>
      </div>

      {message.text && (
        <div className={`mb-4 p-4 rounded-lg ${
          message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
        }`}>
          {message.text}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Nombre de la Cafetería
          </h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nombre
            </label>
            <input
              type="text"
              value={settings.cafeteria_name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Nombre de la cafetería"
            />
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Colores del Tema
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Color Primario
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  value={settings.primary_color}
                  onChange={(e) => handleColorChange('primary_color', e.target.value)}
                  className="w-16 h-10 rounded cursor-pointer border border-gray-300"
                />
                <input
                  type="text"
                  value={settings.primary_color}
                  onChange={(e) => handleColorChange('primary_color', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="#3B82F6"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Color Secundario
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  value={settings.secondary_color}
                  onChange={(e) => handleColorChange('secondary_color', e.target.value)}
                  className="w-16 h-10 rounded cursor-pointer border border-gray-300"
                />
                <input
                  type="text"
                  value={settings.secondary_color}
                  onChange={(e) => handleColorChange('secondary_color', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="#10B981"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Color de Acento
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  value={settings.accent_color}
                  onChange={(e) => handleColorChange('accent_color', e.target.value)}
                  className="w-16 h-10 rounded cursor-pointer border border-gray-300"
                />
                <input
                  type="text"
                  value={settings.accent_color}
                  onChange={(e) => handleColorChange('accent_color', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="#F59E0B"
                />
              </div>
            </div>
          </div>

          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-3">Vista previa de colores:</p>
            <div className="flex gap-3">
              <div 
                className="w-20 h-20 rounded-lg shadow-md flex items-center justify-center text-white font-semibold"
                style={{ backgroundColor: settings.primary_color }}
              >
                Primario
              </div>
              <div 
                className="w-20 h-20 rounded-lg shadow-md flex items-center justify-center text-white font-semibold"
                style={{ backgroundColor: settings.secondary_color }}
              >
                Secundario
              </div>
              <div 
                className="w-20 h-20 rounded-lg shadow-md flex items-center justify-center text-white font-semibold"
                style={{ backgroundColor: settings.accent_color }}
              >
                Acento
              </div>
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Logo de la Cafetería
          </h2>
          
          {logoPreview && (
            <div className="mb-4 relative inline-block">
              <img 
                src={logoPreview} 
                alt="Logo preview" 
                className="max-w-xs max-h-40 rounded-lg shadow-md"
              />
              <button
                onClick={handleDeleteLogo}
                disabled={loading}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          <div className="flex items-center gap-3">
            <input
              type="file"
              accept="image/*"
              onChange={handleLogoChange}
              className="flex-1 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {logoFile && (
              <button
                onClick={handleUploadLogo}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Subir Logo
              </button>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Formatos aceptados: PNG, JPG, JPEG, GIF, SVG, WEBP
          </p>
        </div>

        <div className="flex justify-end pt-4 border-t">
          <button
            onClick={handleSaveSettings}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {loading ? 'Guardando...' : 'Guardar Configuración'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Settings
