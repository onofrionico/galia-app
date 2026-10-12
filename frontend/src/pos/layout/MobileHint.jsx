import { useState } from 'react'
import { Link } from 'react-router-dom'

const KEY = 'pos.mobileHintDismissed'

function initiallyVisible() {
  try {
    return window.matchMedia('(max-width: 767px)').matches && localStorage.getItem(KEY) !== '1'
  } catch {
    return false
  }
}

// En un celular, la caja sugiere la vista del Camarero (sin forzarla).
export default function MobileHint() {
  const [visible, setVisible] = useState(initiallyVisible)
  if (!visible) return null

  const dismiss = () => {
    try {
      localStorage.setItem(KEY, '1')
    } catch {
      // Sin storage: el aviso se oculta solo por ahora.
    }
    setVisible(false)
  }

  return (
    <div className="flex items-center gap-3 bg-galia-lime/40 px-4 py-2 text-sm">
      <span className="flex-1">
        ¿Estás en el celular? <Link to="/camarero" className="font-semibold underline">Abrí la vista Camarero</Link>
      </span>
      <button type="button" aria-label="Cerrar aviso" className="min-h-[40px] px-2" onClick={dismiss}>×</button>
    </div>
  )
}
