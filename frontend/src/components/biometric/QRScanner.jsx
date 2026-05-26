import { useState, useEffect, useRef } from 'react'
import jsQR from 'jsqr'
import { AlertCircle } from 'lucide-react'

const QRScanner = ({ onQRScanned }) => {
  const [error, setError] = useState(null)
  const [scanning, setScanning] = useState(true)
  const [useManualInput, setUseManualInput] = useState(false)
  const [manualToken, setManualToken] = useState('')
  const videoRef = useRef(null)
  const canvasRef = useRef(null)

  useEffect(() => {
    if (!scanning || !videoRef.current) return

    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'environment',
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        })

        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
      } catch (err) {
        setError(`No se pudo acceder a la cámara: ${err.message}`)
        setScanning(false)
      }
    }

    startCamera()

    return () => {
      if (videoRef.current?.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop())
      }
    }
  }, [scanning])

  useEffect(() => {
    if (!scanning || !videoRef.current || useManualInput) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const video = videoRef.current

    const scanInterval = setInterval(() => {
      if (video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight

        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const code = jsQR(imageData.data, imageData.width, imageData.height)

        if (code) {
          // Parse QR payload: "biometric://employee_id/token"
          const payload = code.data
          if (payload.startsWith('biometric://')) {
            const parts = payload.replace('biometric://', '').split('/')
            if (parts.length >= 2) {
              const employeeId = parts[0]
              const token = parts[1]

              setScanning(false)
              onQRScanned(token, { employee_id: parseInt(employeeId) })
            }
          }
        }
      }
    }, 300)

    return () => clearInterval(scanInterval)
  }, [scanning, useManualInput, onQRScanned])

  const handleManualSubmit = async (e) => {
    e.preventDefault()
    if (!manualToken.trim()) {
      setError('Por favor ingresa el token QR')
      return
    }

    if (manualToken.trim().length < 10) {
      setError('Token debe tener al menos 10 caracteres')
      return
    }

    setScanning(false)
    onQRScanned(manualToken.trim(), { employee_id: 0 })
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-2">
          <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {!useManualInput ? (
        <>
          {/* Camera View */}
          <div className="relative rounded-lg overflow-hidden bg-black">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="w-full h-80 object-cover"
            />
            <canvas
              ref={canvasRef}
              className="hidden"
            />

            {scanning && (
              <div className="absolute inset-0 border-4 border-blue-400 rounded-lg animate-pulse flex items-center justify-center">
                <div className="text-center">
                  <div className="text-white text-sm font-medium bg-black bg-opacity-50 px-4 py-2 rounded">
                    Apunta al QR
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Fallback to Manual Input */}
          <button
            onClick={() => setUseManualInput(true)}
            className="w-full text-blue-600 hover:text-blue-700 text-sm font-medium py-2 transition"
          >
            No puedo usar la cámara, ingresaré el código manualmente
          </button>
        </>
      ) : (
        <>
          {/* Manual Token Input */}
          <form onSubmit={handleManualSubmit} className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Token QR
              </label>
              <input
                type="text"
                value={manualToken}
                onChange={(e) => setManualToken(e.target.value)}
                placeholder="Ingresa el token del QR"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition"
            >
              Continuar
            </button>
          </form>

          <button
            onClick={() => {
              setUseManualInput(false)
              setManualToken('')
              setScanning(true)
              setError(null)
            }}
            className="w-full text-blue-600 hover:text-blue-700 text-sm font-medium py-2 transition"
          >
            Volver a usar la cámara
          </button>
        </>
      )}
    </div>
  )
}

export default QRScanner
