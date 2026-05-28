import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import configService from '@/services/configService'
import { Upload, Check, AlertCircle } from 'lucide-react'

const BrandingConfig = () => {
  const { isAdmin } = useAuth()

  if (!isAdmin()) {
    return <Navigate to="/dashboard" replace />
  }
  const [logoFile, setLogoFile] = useState(null)
  const [backgroundFile, setBackgroundFile] = useState(null)
  const [currentConfig, setCurrentConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)
  const [logoPreview, setLogoPreview] = useState(null)
  const [backgroundPreview, setBackgroundPreview] = useState(null)

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const config = await configService.getBrandingConfig()
        setCurrentConfig(config)
      } catch (error) {
        console.error('Error loading config:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchConfig()
  }, [])

  const handleLogoChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setLogoFile(file)
      const reader = new FileReader()
      reader.onload = (event) => setLogoPreview(event.target.result)
      reader.readAsDataURL(file)
    }
  }

  const handleBackgroundChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setBackgroundFile(file)
      const reader = new FileReader()
      reader.onload = (event) => setBackgroundPreview(event.target.result)
      reader.readAsDataURL(file)
    }
  }

  const handleSave = async () => {
    if (!logoFile && !backgroundFile) {
      setMessage({ type: 'warning', text: 'Select at least one file to upload' })
      return
    }

    try {
      setSaving(true)
      setMessage(null)

      const updatedConfig = await configService.updateBrandingConfig(logoFile, backgroundFile)
      setCurrentConfig(updatedConfig)
      setLogoFile(null)
      setBackgroundFile(null)
      setLogoPreview(null)
      setBackgroundPreview(null)
      setMessage({ type: 'success', text: 'Branding configuration updated successfully!' })
    } catch (error) {
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to update configuration' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="p-6 text-center">Loading...</div>
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-2">Configuración de Branding</h1>
      <p className="text-gray-600 mb-8">Sube el logo y la imagen de fondo para personalizar la cafetería.</p>

      {message && (
        <div className={`mb-6 p-4 rounded-lg flex items-start space-x-3 ${
          message.type === 'success' ? 'bg-green-50 border border-green-200' :
          message.type === 'error' ? 'bg-red-50 border border-red-200' :
          'bg-yellow-50 border border-yellow-200'
        }`}>
          {message.type === 'success' ? (
            <Check className="h-5 w-5 text-green-600 mt-0.5" />
          ) : (
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
          )}
          <p className={`text-sm font-medium ${
            message.type === 'success' ? 'text-green-900' :
            message.type === 'error' ? 'text-red-900' :
            'text-yellow-900'
          }`}>
            {message.text}
          </p>
        </div>
      )}

      <div className="space-y-8">
        {/* Logo Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
          <h2 className="text-xl font-semibold mb-4">Logo de Cafetería</h2>

          {currentConfig?.logo_path && !logoPreview && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 font-medium">Logo Actual:</p>
              <img
                src={currentConfig.logo_path}
                alt="Current Logo"
                className="h-24 mt-2 object-contain"
              />
            </div>
          )}

          <label className="flex flex-col items-center justify-center cursor-pointer hover:bg-gray-50 p-6 rounded-lg transition">
            <Upload className="h-8 w-8 text-gray-400 mb-2" />
            <span className="text-gray-600 font-medium">Click to upload logo</span>
            <span className="text-sm text-gray-500 mt-1">PNG, JPG, SVG (recomendado)</span>
            <input
              type="file"
              accept="image/*"
              onChange={handleLogoChange}
              className="hidden"
            />
          </label>

          {logoPreview && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 font-medium mb-2">Preview:</p>
              <img
                src={logoPreview}
                alt="Logo Preview"
                className="h-24 object-contain"
              />
            </div>
          )}
        </div>

        {/* Background Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8">
          <h2 className="text-xl font-semibold mb-4">Fondo del Banner</h2>

          {currentConfig?.banner_background_path && !backgroundPreview && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 font-medium">Fondo Actual:</p>
              <img
                src={currentConfig.banner_background_path}
                alt="Current Background"
                className="h-24 mt-2 object-cover w-full rounded"
              />
            </div>
          )}

          <label className="flex flex-col items-center justify-center cursor-pointer hover:bg-gray-50 p-6 rounded-lg transition">
            <Upload className="h-8 w-8 text-gray-400 mb-2" />
            <span className="text-gray-600 font-medium">Click to upload background</span>
            <span className="text-sm text-gray-500 mt-1">PNG, JPG (opcional)</span>
            <input
              type="file"
              accept="image/*"
              onChange={handleBackgroundChange}
              className="hidden"
            />
          </label>

          {backgroundPreview && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 font-medium mb-2">Preview:</p>
              <img
                src={backgroundPreview}
                alt="Background Preview"
                className="h-24 object-cover w-full rounded"
              />
            </div>
          )}
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition"
        >
          {saving ? 'Guardando...' : 'Guardar Cambios'}
        </button>
      </div>
    </div>
  )
}

export default BrandingConfig
