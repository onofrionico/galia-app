import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { ArrowLeft, Camera, MapPin } from 'lucide-react'
import QRScanner from '@/components/biometric/QRScanner'
import BiometricVerification from '@/components/biometric/BiometricVerification'

const BiometricCheckIn = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [step, setStep] = useState('qr_scan')  // 'qr_scan', 'verification', 'success', 'error'
  const [qrToken, setQrToken] = useState(null)
  const [employeeInfo, setEmployeeInfo] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)

  useEffect(() => {
    if (!user) {
      navigate('/login')
    }
  }, [user, navigate])

  const handleQRScanned = (token, employeeData) => {
    setQrToken(token)
    setEmployeeInfo(employeeData)
    setStep('verification')
  }

  const handleVerificationSuccess = (message, entryType) => {
    setSuccessMessage(`${message} (${entryType === 'in' ? 'Entrada' : 'Salida'})`)
    setStep('success')
  }

  const handleVerificationError = (error) => {
    setErrorMessage(error)
    setStep('error')
  }

  const handleReset = () => {
    setStep('qr_scan')
    setQrToken(null)
    setEmployeeInfo(null)
    setSuccessMessage(null)
    setErrorMessage(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => navigate('/time-tracking')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition"
          >
            <ArrowLeft size={20} />
            <span className="text-sm font-medium">Volver</span>
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Fichar Biométrico</h1>
          <div className="w-12" />
        </div>

        {/* Content based on step */}
        <div className="bg-white rounded-lg shadow-lg p-6 min-h-96">
          {step === 'qr_scan' && (
            <div>
              <p className="text-gray-600 text-center mb-6">
                Escanea el código QR para comenzar
              </p>
              <QRScanner onQRScanned={handleQRScanned} />
            </div>
          )}

          {step === 'verification' && qrToken && (
            <div>
              <BiometricVerification
                qrToken={qrToken}
                employeeInfo={employeeInfo}
                onSuccess={handleVerificationSuccess}
                onError={handleVerificationError}
              />
            </div>
          )}

          {step === 'success' && (
            <div className="text-center py-8">
              <div className="mb-4">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
                  <div className="text-3xl">✓</div>
                </div>
              </div>
              <h2 className="text-2xl font-bold text-green-600 mb-2">¡Registro Exitoso!</h2>
              <p className="text-gray-600 mb-6">{successMessage}</p>
              <button
                onClick={handleReset}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition"
              >
                Escanear Otro QR
              </button>
            </div>
          )}

          {step === 'error' && (
            <div className="text-center py-8">
              <div className="mb-4">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
                  <div className="text-3xl">✕</div>
                </div>
              </div>
              <h2 className="text-2xl font-bold text-red-600 mb-2">Error al Registrar</h2>
              <p className="text-gray-600 mb-6">{errorMessage}</p>
              <button
                onClick={handleReset}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition"
              >
                Intentar de Nuevo
              </button>
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="mt-6 text-center text-sm text-gray-600">
          <p className="flex items-center justify-center gap-2 mb-2">
            <Camera size={16} /> Requiere acceso a cámara
          </p>
          <p className="flex items-center justify-center gap-2">
            <MapPin size={16} /> Requiere acceso a ubicación GPS
          </p>
        </div>
      </div>
    </div>
  )
}

export default BiometricCheckIn
