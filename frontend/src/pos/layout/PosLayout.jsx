import { Outlet } from 'react-router-dom'
import { usePosChanges } from '../hooks/usePosChanges'
import { ToastProvider } from '../ui/Toasts'
import MobileHint from './MobileHint'
import PosTopBar from './PosTopBar'

function PosShell() {
  usePosChanges()
  return (
    <div className="flex h-screen flex-col bg-galia-cream">
      <PosTopBar />
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
