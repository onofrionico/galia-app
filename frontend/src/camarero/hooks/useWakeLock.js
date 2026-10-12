import { useEffect } from 'react'

// Mantiene la pantalla encendida mientras la app está visible (si el navegador lo soporta).
// El navegador suelta el bloqueo al ocultarse la página; se vuelve a pedir al volver al frente.
export function useWakeLock() {
  useEffect(() => {
    if (!('wakeLock' in navigator)) return undefined
    let lock = null
    let cancelled = false

    const request = async () => {
      if (document.visibilityState !== 'visible') return
      try {
        lock = await navigator.wakeLock.request('screen')
        if (cancelled) lock.release().catch(() => {})
      } catch {
        lock = null
      }
    }
    const onVisibility = () => {
      if (document.visibilityState === 'visible') request()
    }

    request()
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      cancelled = true
      document.removeEventListener('visibilitychange', onVisibility)
      lock?.release().catch(() => {})
    }
  }, [])
}
