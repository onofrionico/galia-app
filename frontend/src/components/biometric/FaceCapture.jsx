import { useState, useEffect, useRef } from 'react'
import { AlertCircle } from 'lucide-react'

const FaceCapture = ({ onPhotoCapture, gpsData }) => {
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)

  useEffect(() => {
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 640 },
            height: { ideal: 480 }
          }
        })

        if (videoRef.current) {
          videoRef.current.srcObject = stream
          streamRef.current = stream
        }

        setLoading(false)
      } catch (err) {
        setError(`No se pudo acceder a la cámara: ${err.message}`)
        setLoading(false)
      }
    }

    startCamera()

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  const handleCapture = () => {
    const video = videoRef.current
    const canvas = canvasRef.current

    if (!video || !canvas) return

    // Set canvas size to match video dimensions
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // Draw video frame to canvas
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)

    // Convert to base64 JPEG
    const photoBase64 = canvas.toDataURL('image/jpeg', 0.8)

    // For MVP: Calculate simple "confidence" based on image properties
    // In production, this would call AWS Rekognition or face_recognition library
    const confidence = calculateMockConfidence(canvas, ctx)

    onPhotoCapture(photoBase64, confidence)
  }

  const calculateMockConfidence = (canvas, ctx) => {
    // Get image data to analyze
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const data = imageData.data

    // Calculate average brightness (0-255)
    let totalBrightness = 0
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i]
      const g = data[i + 1]
      const b = data[i + 2]
      totalBrightness += (r + g + b) / 3
    }
    const avgBrightness = totalBrightness / (data.length / 4)

    // Calculate variance in color channels (edge detection proxy)
    let variance = 0
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i] - avgBrightness
      variance += r * r
    }
    variance = Math.sqrt(variance / (data.length / 4))

    // Mock confidence score based on lighting and detail
    // Good lighting: brightness between 50-200
    // Good detail: variance > 30
    let confidence = 0.5

    if (avgBrightness > 40 && avgBrightness < 220) {
      confidence += 0.2
    }

    if (variance > 25) {
      confidence += 0.3
    }

    return Math.min(0.95, Math.max(0.6, confidence))
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <p className="text-gray-600">Iniciando cámara...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-2">
          <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {!error && (
        <>
          {/* Video Stream */}
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

            {/* Face Detection Overlay */}
            <div className="absolute inset-0 border-4 border-blue-400 rounded-lg m-8"></div>
            <div className="absolute bottom-4 left-4 right-4 bg-black bg-opacity-50 text-white text-center text-sm py-2 rounded">
              Mira a la cámara
            </div>
          </div>

          {/* GPS Status */}
          {gpsData && (
            <div className="bg-green-50 p-3 rounded-lg">
              <p className="text-sm text-green-900 flex items-center gap-2">
                <span className="text-lg">✓</span>
                Ubicación capturada ({gpsData.accuracy.toFixed(1)}m de precisión)
              </p>
            </div>
          )}

          {/* Capture Button */}
          <button
            onClick={handleCapture}
            className="w-full bg-blue-600 text-white px-4 py-3 rounded-lg font-medium hover:bg-blue-700 transition flex items-center justify-center gap-2"
          >
            <span className="text-2xl">📷</span>
            Capturar Foto
          </button>
        </>
      )}
    </div>
  )
}

export default FaceCapture
