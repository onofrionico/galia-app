import { useEffect, useRef } from 'react'

let counter = 0

// En el celular, el "atrás" del teléfono cierra la hoja abierta en lugar de salir de la pantalla.
// Cada hoja agrega una entrada al historial (conservando idx/key/usr de React Router, así el router no
// ve un cambio de ruta) y la quita al cerrarse con su botón. El retiro se difiere un tick: en desarrollo,
// StrictMode monta dos veces y un history.back() inmediato cerraría la hoja recién montada.
export function useBackToClose(enabled, onClose) {
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    if (!enabled) return undefined
    counter += 1
    const id = `pos-sheet-${counter}`
    window.history.pushState({ ...window.history.state, posSheet: id }, '')
    let closedByBack = false
    const onPop = () => {
      if (window.history.state?.posSheet !== id) {
        closedByBack = true
        onCloseRef.current()
      }
    }
    window.addEventListener('popstate', onPop)
    return () => {
      window.removeEventListener('popstate', onPop)
      if (closedByBack) return
      setTimeout(() => {
        if (window.history.state?.posSheet === id) window.history.back()
      }, 0)
    }
  }, [enabled])
}
