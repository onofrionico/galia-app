import { useState, useEffect } from 'react'
import { notificationService } from '../../services/notificationService'
import { useNotification } from '../../context/NotificationContext'

const NotificationPreferences = () => {
  const { addNotification } = useNotification()
  const [preferences, setPreferences] = useState({
    comanda_enabled: true,
    venta_cerrada_enabled: true,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadPreferences()
  }, [])

  const loadPreferences = async () => {
    try {
      setLoading(true)
      const data = await notificationService.getPreferences()
      setPreferences(data)
    } catch (error) {
      console.error('Error loading preferences:', error)
      addNotification('Error al cargar preferencias', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = (key) => {
    setPreferences((prev) => ({
      ...prev,
      [key]: !prev[key],
    }))
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      await notificationService.updatePreferences(preferences)
      addNotification('Preferencias guardadas', 'success')
    } catch (error) {
      console.error('Error saving preferences:', error)
      addNotification('Error al guardar preferencias', 'error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="inline-block">Cargando preferencias...</div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6 text-gray-900">Preferencias de Notificaciones</h2>

      <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
        {/* Comanda Enabled */}
        <div className="flex items-center justify-between p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors">
          <div className="flex-1">
            <label className="block text-sm font-semibold text-gray-900">
              Notificaciones de Comandas
            </label>
            <p className="text-sm text-gray-600 mt-1">
              Recibe alertas cuando se imprime una nueva comanda
            </p>
          </div>
          <div className="flex-shrink-0">
            <button
              onClick={() => handleToggle('comanda_enabled')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                preferences.comanda_enabled ? 'bg-green-500' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.comanda_enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Venta Cerrada Enabled */}
        <div className="flex items-center justify-between p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors">
          <div className="flex-1">
            <label className="block text-sm font-semibold text-gray-900">
              Notificaciones de Ventas Cerradas
            </label>
            <p className="text-sm text-gray-600 mt-1">
              Recibe alertas cuando se cierra una venta
            </p>
          </div>
          <div className="flex-shrink-0">
            <button
              onClick={() => handleToggle('venta_cerrada_enabled')}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                preferences.venta_cerrada_enabled ? 'bg-green-500' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences.venta_cerrada_enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="mt-6 flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
        >
          {saving ? 'Guardando...' : 'Guardar Cambios'}
        </button>
      </div>
    </div>
  )
}

export default NotificationPreferences
