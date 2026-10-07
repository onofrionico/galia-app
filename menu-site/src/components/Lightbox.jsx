import { useEffect } from 'react'

export default function Lightbox({ item, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div role="dialog" aria-modal="true" aria-label={item.name} onClick={onClose} className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-plum-dark/90 p-4">
      <img src={item.image} alt={item.name} className="max-h-[80vh] max-w-full rounded-xl object-contain" />
      <p className="mt-3 font-display text-2xl uppercase text-cream">{item.name}</p>
      <button type="button" onClick={onClose} className="mt-2 text-sm text-cream underline">Cerrar</button>
    </div>
  )
}
