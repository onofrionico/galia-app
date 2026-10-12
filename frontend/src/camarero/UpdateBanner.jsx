import { useRegisterSW } from 'virtual:pwa-register/react'
import { btn } from '@/pos/ui/buttons'

const UPDATE_CHECK_MS = 60 * 60 * 1000

// Registra el service worker del Camarero y avisa cuando hay una versión nueva del frontend (se revisa cada
// hora, no solo al abrir). Va abajo, fija, para no sumar otro margen superior; se descarta con "×".
export default function UpdateBanner() {
  const { needRefresh: [needRefresh, setNeedRefresh], updateServiceWorker } = useRegisterSW({
    onRegisteredSW(swUrl, registration) {
      if (registration) setInterval(() => registration.update(), UPDATE_CHECK_MS)
    },
  })
  if (!needRefresh) return null
  return (
    <div className="fixed inset-x-0 bottom-0 z-[50] flex items-center justify-between gap-3 bg-galia-lime px-4 pt-2 pb-[calc(env(safe-area-inset-bottom)+0.5rem)] text-sm shadow-[0_-2px_8px_rgba(0,0,0,0.15)]">
      <span>Hay una versión nueva</span>
      <span className="flex items-center gap-2">
        <button type="button" className={btn('primary', 'min-h-[40px]')} onClick={() => updateServiceWorker(true)}>
          Actualizar
        </button>
        <button type="button" aria-label="Más tarde" className="min-h-[40px] px-2" onClick={() => setNeedRefresh(false)}>×</button>
      </span>
    </div>
  )
}
