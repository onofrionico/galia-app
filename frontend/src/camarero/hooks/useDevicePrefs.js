import { useCallback, useState } from 'react'

const KEY = 'camarero.prefs'
const DEFAULTS = { salonId: null, view: 'list', filter: 'all' }

function read() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) ?? '{}') }
  } catch {
    return DEFAULTS
  }
}

// Salón, vista (Lista/Plano) y filtro (Todas/Mías) de este celular.
export function useDevicePrefs() {
  const [prefs, setPrefs] = useState(read)
  const update = useCallback((patch) => {
    setPrefs((current) => {
      const next = { ...current, ...patch }
      try {
        localStorage.setItem(KEY, JSON.stringify(next))
      } catch {
        // Sin storage: las preferencias duran mientras la app está abierta.
      }
      return next
    })
  }, [])
  return [prefs, update]
}
