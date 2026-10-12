import { Outlet } from 'react-router-dom'
import { usePosChanges } from '@/pos/hooks/usePosChanges'
import { ModalPresentationContext } from '@/pos/ui/ModalPresentation'
import { ToastProvider } from '@/pos/ui/Toasts'
import ConnectivityBanner from './ConnectivityBanner'
import { useConnectivity } from './hooks/useConnectivity'
import { useWakeLock } from './hooks/useWakeLock'

function CamareroShell() {
  const { online, report } = useConnectivity()
  usePosChanges({ onResult: report })
  useWakeLock()
  return (
    <div className="flex h-dvh flex-col bg-galia-cream">
      <ConnectivityBanner online={online} />
      <main className="min-h-0 flex-1">
        <Outlet />
      </main>
    </div>
  )
}

// Vista del celular: los modales del POS se dibujan como hojas inferiores.
export default function CamareroLayout() {
  return (
    <ToastProvider>
      <ModalPresentationContext.Provider value="sheet">
        <CamareroShell />
      </ModalPresentationContext.Provider>
    </ToastProvider>
  )
}
