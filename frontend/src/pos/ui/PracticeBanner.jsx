import { useCutover } from '../hooks/useCutover'

// Franja bien visible mientras Galia está en modo práctica.
export default function PracticeBanner() {
  const { practice_mode: practiceMode } = useCutover()
  if (!practiceMode) return null
  return (
    <div role="status" className="bg-amber-400 px-4 py-1.5 text-center text-sm font-bold uppercase tracking-wide text-amber-950">
      PRÁCTICA: nada de esto cuenta
    </div>
  )
}
