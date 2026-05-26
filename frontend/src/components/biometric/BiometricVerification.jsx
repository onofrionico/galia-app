import { useState, useEffect } from 'react'
import { AlertCircle, MapPin, Camera, CheckCircle } from 'lucide-react'
import biometricService from '@/services/biometricService'
import QRScanner from './QRScanner'
import GPSCapture from './GPSCapture'
import FaceCapture from './FaceCapture'

const BiometricVerification = ({ qrToken, employeeInfo, onSuccess, onError }) => {
  const [step, setStep] = useState('permissions')  // 'permissions', 'capture', 'verify', 'entry_selection', 'submitting'
  const [cameraPermission, setCameraPermission] = useState(null)
  const [gpsPermission, setGpsPermission] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Captured data
  const [gpsData, setGpsData] = useState(null)
  const [photoBase64, setPhotoBase64] = useState(null)
  const [biometricConfidence, setBiometricConfidence] = useState(0)
  const [biometricVerified, setBiometricVerified] = useState(false)
  const [entryType, setEntryType] = useState('in')  // 'in' or 'out'

  useEffect(() => {
    validateQRToken()
  }, [qrToken])

  const validateQRToken = async () => {
    try {
      await biometricService.validateQRToken(qrToken)
    } catch (err) {
      onError(err.message || 'Token QR inválido')
    }
  }

  const handleRequestPermissions = async () => {
    setLoading(true)
    setError(null)

    try {
      // Request camera permission
      const cameraStream = await navigator.mediaDevices.getUserMedia({ video: true })
      setCameraPermission(true)
      cameraStream.getTracks().forEach(track => track.stop())

      // Request GPS permission
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setGpsPermission(true)
          setGpsData({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: new Date()
          })
        },
        (err) => {
          setGpsPermission(false)
          setError('No se pudo acceder a la ubicación GPS')
        }
      )

      setStep('capture')
    } catch (err) {
      setError(err.message || 'Error al solicitar permisos')
    } finally {
      setLoading(false)
    }
  }

  const handlePhotoCapture = (base64Photo, confidence) => {
    setPhotoBase64(base64Photo)
    setBiometricConfidence(confidence)
    setBiometricVerified(confidence >= 0.85)  // Threshold
    setStep('verify')
  }

  const handleVerifyRetry = () => {
    setPhotoBase64(null)
    setBiometricConfidence(0)
    setBiometricVerified(false)
    setStep('capture')
  }

  const handleEntryTypeSelect = (type) => {
    setEntryType(type)
    setStep('entry_selection')
  }

  const handleRetryFromError = () => {
    setError(null)
    setPhotoBase64(null)
    setBiometricConfidence(0)
    setBiometricVerified(false)
    setStep('capture')
  }

  const handleSubmit = async () => {
    if (!photoBase64 || !gpsData || !biometricVerified) {
      setError('Faltan datos requeridos')
      return
    }

    setLoading(true)
    setError(null)

    try {
      setStep('submitting')

      const response = await biometricService.checkIn({
        qr_token: qrToken,
        entry_type: entryType,
        photo_base64: photoBase64,
        latitude: gpsData.latitude,
        longitude: gpsData.longitude,
        accuracy: gpsData.accuracy,
        biometric_confidence: biometricConfidence,
        biometric_verified: biometricVerified,
      })

      onSuccess(response.message, entryType)
    } catch (err) {
      onError(err.message || 'Error al registrar entrada')
      setStep('entry_selection')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Progress Indicators */}
      <div className="flex justify-between items-center">
        <div className={`flex-1 text-center ${step === 'permissions' ? 'font-bold text-blue-600' : 'text-gray-500'}`}>
          1. Permisos
        </div>
        <div className={`flex-1 text-center ${step === 'capture' ? 'font-bold text-blue-600' : 'text-gray-500'}`}>
          2. Captura
        </div>
        <div className={`flex-1 text-center ${step === 'verify' || step === 'entry_selection' ? 'font-bold text-blue-600' : 'text-gray-500'}`}>
          3. Verificación
        </div>
      </div>

      {/* Step Content */}
      {step === 'permissions' && (
        <div className="space-y-4">
          <p className="text-gray-700 text-center font-medium">
            Esta aplicación necesita acceso a:
          </p>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Camera size={24} className="text-blue-600" />
              <span className="text-gray-700">Acceso a cámara</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <MapPin size={24} className="text-blue-600" />
              <span className="text-gray-700">Acceso a ubicación GPS</span>
            </div>
          </div>
          <button
            onClick={handleRequestPermissions}
            disabled={loading}
            className="w-full bg-blue-600 text-white px-4 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 transition"
          >
            {loading ? 'Solicitando permisos...' : 'Permitir Acceso'}
          </button>
        </div>
      )}

      {step === 'capture' && (
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Capturar Foto</h3>
            <FaceCapture
              onPhotoCapture={handlePhotoCapture}
              gpsData={gpsData}
            />
          </div>
          {gpsData && (
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-900">
                <strong>Ubicación:</strong> {gpsData.latitude.toFixed(4)}, {gpsData.longitude.toFixed(4)}
              </p>
              <p className="text-sm text-blue-900">
                <strong>Precisión:</strong> {gpsData.accuracy.toFixed(1)}m
              </p>
            </div>
          )}
        </div>
      )}

      {step === 'verify' && (
        <div className="space-y-4">
          {photoBase64 && (
            <div className="space-y-3">
              <div className="border-2 border-gray-200 rounded-lg overflow-hidden">
                <img
                  src={photoBase64}
                  alt="Foto capturada"
                  className="w-full h-auto"
                />
              </div>
              <div className={`p-4 rounded-lg ${biometricVerified ? 'bg-green-50' : 'bg-yellow-50'}`}>
                <p className={`font-medium ${biometricVerified ? 'text-green-900' : 'text-yellow-900'}`}>
                  {biometricVerified ? '✓ Identidad Verificada' : '⚠ Verifica tu cara en la cámara'}
                </p>
                <p className={`text-sm ${biometricVerified ? 'text-green-700' : 'text-yellow-700'}`}>
                  Confianza: {(biometricConfidence * 100).toFixed(0)}%
                </p>
              </div>

              {biometricVerified ? (
                <div className="space-y-2">
                  <p className="text-sm text-gray-600 text-center">¿Qué tipo de registro?</p>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => handleEntryTypeSelect('in')}
                      className="bg-green-100 border-2 border-green-500 text-green-700 px-4 py-3 rounded-lg font-medium hover:bg-green-200 transition"
                    >
                      Entrada
                    </button>
                    <button
                      onClick={() => handleEntryTypeSelect('out')}
                      className="bg-orange-100 border-2 border-orange-500 text-orange-700 px-4 py-3 rounded-lg font-medium hover:bg-orange-200 transition"
                    >
                      Salida
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={handleVerifyRetry}
                  className="w-full bg-yellow-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-yellow-700 transition"
                >
                  Intentar Nuevamente
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {step === 'entry_selection' && (
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg space-y-2">
            <p className="text-sm"><strong>Tipo:</strong> {entryType === 'in' ? 'Entrada' : 'Salida'}</p>
            <p className="text-sm"><strong>Ubicación:</strong> {gpsData?.latitude.toFixed(4)}, {gpsData?.longitude.toFixed(4)}</p>
            <p className="text-sm"><strong>Confianza:</strong> {(biometricConfidence * 100).toFixed(0)}%</p>
          </div>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-green-600 text-white px-4 py-3 rounded-lg font-medium hover:bg-green-700 disabled:bg-gray-400 transition"
          >
            {loading ? 'Registrando...' : 'Confirmar Registro'}
          </button>
          <button
            onClick={handleVerifyRetry}
            className="w-full border-2 border-gray-300 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-50 transition"
          >
            Cancelar
          </button>
        </div>
      )}

      {step === 'submitting' && (
        <div className="flex flex-col items-center justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Registrando entrada...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-2">
          <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
          <p className="text-sm">{error}</p>
        </div>
      )}
    </div>
  )
}

export default BiometricVerification
