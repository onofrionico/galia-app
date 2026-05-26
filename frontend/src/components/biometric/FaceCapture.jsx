import { useState, useEffect, useRef } from 'react'
import { AlertCircle } from 'lucide-react'
import * as faceapi from '@vladmandic/face-api'

const FaceCapture = ({ onPhotoCapture, gpsData }) => {
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [detectedFaces, setDetectedFaces] = useState(0)
  const [faceDetectionStatus, setFaceDetectionStatus] = useState('Cargando modelo...')
  const [modelsLoaded, setModelsLoaded] = useState(false)
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const detectionIntervalRef = useRef(null)

  useEffect(() => {
    const initializeFaceDetection = async () => {
      try {
        // Load face detection models from CDN
        const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model/'
        await faceapi.nets.tinyFaceDetector.load(MODEL_URL)
        await faceapi.nets.faceLandmark68Net.load(MODEL_URL)
        await faceapi.nets.faceExpressionNet.load(MODEL_URL)
        setModelsLoaded(true)
        setFaceDetectionStatus('Listo para detectar rostros')

        // Start camera
        await startCamera()
      } catch (err) {
        setError(`Error cargando modelos de detección: ${err.message}`)
        setLoading(false)
      }
    }

    initializeFaceDetection()

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      if (detectionIntervalRef.current) {
        clearInterval(detectionIntervalRef.current)
      }
    }
  }, [])

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

      // Start continuous face detection
      startFaceDetection()
      setLoading(false)
    } catch (err) {
      setError(`No se pudo acceder a la cámara: ${err.message}`)
      setLoading(false)
    }
  }

  const startFaceDetection = () => {
    detectionIntervalRef.current = setInterval(async () => {
      const video = videoRef.current
      if (!video || !modelsLoaded) return

      try {
        // Detect faces in real-time
        const detections = await faceapi
          .detectAllFaces(video, new faceapi.TinyFaceDetectorOptions())
          .withFaceLandmarks()
          .withFaceExpressions()

        setDetectedFaces(detections.length)

        if (detections.length === 0) {
          setFaceDetectionStatus('No se detecta rostro')
        } else if (detections.length === 1) {
          setFaceDetectionStatus('✓ Un rostro detectado')
        } else {
          setFaceDetectionStatus(`⚠ ${detections.length} rostros detectados`)
        }
      } catch (err) {
        // Silently handle detection errors
      }
    }, 300)
  }

  const handleCapture = async () => {
    const video = videoRef.current
    const canvas = canvasRef.current

    if (!video || !canvas) return

    // Check if exactly one face is detected
    try {
      const detections = await faceapi
        .detectAllFaces(video, new faceapi.TinyFaceDetectorOptions())
        .withFaceLandmarks()
        .withFaceExpressions()

      if (detections.length === 0) {
        setError('No se detecta rostro. Asegúrate de estar mirando a la cámara.')
        return
      }

      if (detections.length > 1) {
        setError(`Se detectaron ${detections.length} rostros. Solo debe haber uno.`)
        return
      }

      // One face detected - capture photo
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight

      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)

      const photoBase64 = canvas.toDataURL('image/jpeg', 0.8)

      // Get confidence from face detection
      const detection = detections[0]
      const confidence = detection.detection.score

      onPhotoCapture(photoBase64, confidence)
    } catch (err) {
      setError('Error al capturar foto. Intenta de nuevo.')
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
        <p className="text-gray-600">Inicializando cámara y modelos...</p>
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
            <div className={`absolute inset-0 border-4 rounded-lg m-8 transition-colors ${
              detectedFaces === 1 ? 'border-green-400' : 'border-blue-400'
            }`}></div>

            {/* Status Display */}
            <div className="absolute top-4 left-4 right-4 bg-black bg-opacity-70 text-white text-center text-sm py-2 rounded">
              {faceDetectionStatus}
            </div>

            <div className="absolute bottom-4 left-4 right-4 bg-black bg-opacity-50 text-white text-center text-sm py-2 rounded">
              {detectedFaces === 0 ? 'Mira a la cámara' : detectedFaces === 1 ? '✓ Listo para capturar' : '⚠ Demasiados rostros'}
            </div>
          </div>

          {/* Face Detection Status */}
          <div className={`p-3 rounded-lg ${
            detectedFaces === 1
              ? 'bg-green-50 text-green-900'
              : detectedFaces === 0
              ? 'bg-yellow-50 text-yellow-900'
              : 'bg-red-50 text-red-900'
          }`}>
            <p className="text-sm font-medium">
              {detectedFaces === 1 && '✓ Rostro detectado correctamente'}
              {detectedFaces === 0 && '⚠ Esperando detectar tu rostro'}
              {detectedFaces > 1 && `✕ Demasiados rostros (${detectedFaces})`}
            </p>
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
            disabled={detectedFaces !== 1}
            className={`w-full px-4 py-3 rounded-lg font-medium transition flex items-center justify-center gap-2 ${
              detectedFaces === 1
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-gray-400 text-gray-200 cursor-not-allowed'
            }`}
          >
            <span className="text-2xl">📷</span>
            {detectedFaces === 1 ? 'Capturar Foto' : 'Detectando rostro...'}
          </button>
        </>
      )}
    </div>
  )
}

export default FaceCapture
