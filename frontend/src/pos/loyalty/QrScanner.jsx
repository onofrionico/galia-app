import { useEffect, useRef, useState } from 'react'
import { Html5Qrcode } from 'html5-qrcode'

// Lee un QR con la cámara trasera. Llama a onScan(texto) una sola vez y se detiene.
export default function QrScanner({ onScan }) {
  const [error, setError] = useState('')
  const done = useRef(false)
  const onScanRef = useRef(onScan)
  onScanRef.current = onScan

  useEffect(() => {
    const scanner = new Html5Qrcode('pos-qr-reader')
    let started = false
    scanner.start({ facingMode: 'environment' }, { fps: 10, qrbox: 220 }, (text) => {
      if (done.current) return
      done.current = true
      onScanRef.current(text)
    }).then(() => { started = true }).catch(() => setError('No se pudo abrir la cámara. Probá escribiendo el nombre.'))
    return () => {
      if (started) scanner.stop().catch(() => {})
    }
  }, [])

  return (
    <div>
      <div id="pos-qr-reader" className="mx-auto w-full max-w-xs overflow-hidden rounded-lg bg-black" />
      {error && <p className="mt-2 text-sm text-amber-700">{error}</p>}
    </div>
  )
}
