import { useState, useEffect } from 'react'
import { AlertCircle, MapPin, RefreshCw } from 'lucide-react'

const GPSCapture = ({ onGPSData }) => {
  const [gpsData, setGpsData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [watching, setWatching] = useState(null)

  useEffect(() => {
    startGPSTracking()

    return () => {
      if (watching !== null) {
        navigator.geolocation.clearWatch(watching)
      }
    }
  }, [])

  const startGPSTracking = () => {
    setLoading(true)
    setError(null)

    if (!navigator.geolocation) {
      setError('Geolocalización no soportada en este navegador')
      setLoading(false)
      return
    }

    // Request one-time location with high accuracy
    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        const data = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          altitude: position.coords.altitude,
          heading: position.coords.heading,
          speed: position.coords.speed,
          timestamp: new Date(position.timestamp)
        }

        setGpsData(data)
        onGPSData?.(data)
        setLoading(false)
      },
      (err) => {
        let errorMsg = 'Error al obtener ubicación'
        switch (err.code) {
          case err.PERMISSION_DENIED:
            errorMsg = 'Permisos de ubicación denegados'
            break
          case err.POSITION_UNAVAILABLE:
            errorMsg = 'Ubicación no disponible'
            break
          case err.TIMEOUT:
            errorMsg = 'Tiempo agotado al obtener ubicación'
            break
          default:
            errorMsg = err.message
        }
        setError(errorMsg)
        setLoading(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    )

    setWatching(watchId)
  }

  const handleRefresh = () => {
    if (watching !== null) {
      navigator.geolocation.clearWatch(watching)
    }
    startGPSTracking()
  }

  return (
    <div className="space-y-3">
      {loading && (
        <div className="flex items-center gap-2 text-blue-600">
          <div className="animate-spin">⟳</div>
          <span className="text-sm">Obteniendo ubicación...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg flex items-start gap-2">
          <AlertCircle size={16} className="flex-shrink-0 mt-0.5" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {gpsData && (
        <div className="bg-blue-50 p-4 rounded-lg space-y-2">
          <div className="flex items-center gap-2 text-blue-900 font-medium">
            <MapPin size={18} />
            <span>Ubicación Actual</span>
          </div>

          <div className="text-sm text-blue-800 space-y-1 ml-6">
            <p><strong>Latitud:</strong> {gpsData.latitude.toFixed(6)}</p>
            <p><strong>Longitud:</strong> {gpsData.longitude.toFixed(6)}</p>
            <p><strong>Precisión:</strong> {gpsData.accuracy.toFixed(1)} metros</p>
            {gpsData.altitude !== null && (
              <p><strong>Altitud:</strong> {gpsData.altitude.toFixed(1)} metros</p>
            )}
            <p className="text-xs text-blue-700 mt-2">
              Última actualización: {gpsData.timestamp.toLocaleTimeString()}
            </p>
          </div>

          <button
            onClick={handleRefresh}
            className="w-full flex items-center justify-center gap-2 mt-3 text-blue-600 hover:text-blue-700 font-medium py-2 transition"
          >
            <RefreshCw size={16} />
            Actualizar Ubicación
          </button>
        </div>
      )}

      {!gpsData && !error && loading && (
        <div className="bg-gray-50 p-4 rounded-lg text-center text-gray-600 text-sm">
          <p>Permitiendo acceso a tu ubicación...</p>
          <p className="text-xs mt-1">Esto puede tomar unos segundos</p>
        </div>
      )}
    </div>
  )
}

export default GPSCapture
