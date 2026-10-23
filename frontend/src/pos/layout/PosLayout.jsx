import { Outlet } from 'react-router-dom'
import { usePosChanges } from '../hooks/usePosChanges'
import PracticeBanner from '../ui/PracticeBanner'
import { readPrintPoint, usePrintAgent } from '../print/usePrintAgent'
import { ToastProvider } from '../ui/Toasts'
import MobileHint from './MobileHint'
import PosTopBar from './PosTopBar'

// Si en esta PC se eligió un punto de impresión (página de Impresión), la caja imprime sus trabajos:
// alcanza con tener la caja abierta. El estado se ve en el indicador "Impresión" de la barra.
function PrintAgent() {
  usePrintAgent({ point: readPrintPoint() })
  return null
}

function PosShell() {
  usePosChanges()
  return (
    <div className="flex h-screen flex-col bg-galia-cream">
      <PrintAgent />
      <PosTopBar />
      <PracticeBanner />
      <MobileHint />
      <main className="min-h-0 flex-1">
        <Outlet />
      </main>
    </div>
  )
}

export default function PosLayout() {
  return (
    <ToastProvider>
      <PosShell />
    </ToastProvider>
  )
}
