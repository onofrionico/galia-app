import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'

// Pila de modales abiertos: Escape cierra solo el de arriba.
const stack = []
const WIDTHS = { sm: 'max-w-sm', md: 'max-w-lg', lg: 'max-w-3xl' }

export default function Modal({ title, onClose, children, footer, size = 'md' }) {
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

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
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4"
      onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}
    >
      <div role="dialog" aria-modal="true" aria-label={title}
        className={`flex max-h-[90vh] w-full ${WIDTHS[size]} flex-col rounded-xl bg-white shadow-xl`}>
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
