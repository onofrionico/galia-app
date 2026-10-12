import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import { useBackToClose } from '../hooks/useBackToClose'
import { useModalPresentation } from './ModalPresentation'

// Pila de modales abiertos: Escape cierra solo el de arriba.
const stack = []
const WIDTHS = { sm: 'max-w-sm', md: 'max-w-lg', lg: 'max-w-3xl' }

const OVERLAY = {
  dialog: 'fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4',
  sheet: 'fixed inset-0 z-40 flex items-end justify-center bg-black/40',
}
const PANEL = {
  dialog: (size) => `flex max-h-[90vh] w-full ${WIDTHS[size]} flex-col rounded-xl bg-white shadow-xl`,
  sheet: () => 'flex max-h-[92vh] w-full flex-col rounded-t-2xl bg-white pb-[env(safe-area-inset-bottom)] shadow-xl',
}

export default function Modal({ title, onClose, children, footer, size = 'md' }) {
  const presentation = useModalPresentation()
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose
  useBackToClose(presentation === 'sheet', onClose)

  useEffect(() => {
    const entry = {}
    stack.push(entry)
    const onKey = (event) => {
      if (event.key === 'Escape' && stack[stack.length - 1] === entry) onCloseRef.current()
    }
    window.addEventListener('keydown', onKey)
    return () => {
      stack.splice(stack.indexOf(entry), 1)
      window.removeEventListener('keydown', onKey)
    }
  }, [])

  return (
    <div
      className={OVERLAY[presentation]}
      onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}
    >
      <div role="dialog" aria-modal="true" aria-label={title} className={PANEL[presentation](size)}>
        <div className="flex items-center justify-between border-b px-5 py-3">
          <h2 className="text-lg font-semibold text-galia-plum">{title}</h2>
          <button type="button" onClick={onClose} aria-label="Cerrar" className="rounded-lg p-2 hover:bg-gray-100">
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
        {footer && <div className="border-t px-5 py-3">{footer}</div>}
      </div>
    </div>
  )
}
