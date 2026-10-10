import { createContext, useCallback, useContext, useMemo, useState } from 'react'

const ToastContext = createContext(null)
const STYLES = {
  error: 'bg-red-700 text-white',
  info: 'bg-galia-plum text-galia-cream',
  success: 'bg-green-700 text-white',
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const dismiss = useCallback((id) => setToasts((list) => list.filter((t) => t.id !== id)), [])
  const show = useCallback((kind, message, action) => {
    const id = `${Date.now()}-${Math.random()}`
    setToasts((list) => [...list.slice(-3), { id, kind, message, action }])
    setTimeout(() => dismiss(id), action ? 8000 : 4000)
  }, [dismiss])
  const toast = useMemo(() => ({
    error: (message, action) => show('error', message, action),
    info: (message) => show('info', message),
    success: (message) => show('success', message),
  }), [show])

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed bottom-4 left-1/2 z-50 flex w-[min(90vw,480px)] -translate-x-1/2 flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm shadow-lg ${STYLES[t.kind]}`}>
            <span className="flex-1">{t.message}</span>
            {t.action && (
              <button type="button" className="font-semibold underline"
                onClick={() => { dismiss(t.id); t.action.onClick() }}>
                {t.action.label}
              </button>
            )}
            <button type="button" aria-label="Cerrar aviso" onClick={() => dismiss(t.id)}>×</button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast se usa dentro de ToastProvider')
  return context
}
