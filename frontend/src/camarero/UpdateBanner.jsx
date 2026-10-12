import { useRegisterSW } from 'virtual:pwa-register/react'
import { btn } from '@/pos/ui/buttons'

// Registra el service worker del Camarero y avisa cuando hay una versión nueva del frontend.
export default function UpdateBanner() {
  const { needRefresh: [needRefresh, setNeedRefresh], updateServiceWorker } = useRegisterSW()
  if (!needRefresh) return null
  return (
    <div className="flex items-center justify-between gap-3 bg-galia-lime/40 px-4 py-2 pt-[calc(env(safe-area-inset-top)+0.5rem)] text-sm">
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
