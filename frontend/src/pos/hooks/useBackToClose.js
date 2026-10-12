import { useEffect, useRef } from 'react'

let counter = 0
// Ids de entradas de historial cuyo efecto ya se limpió pero que todavía no se retiraron (retiro diferido).
const pendingRemoval = new Set()

// En el celular, el "atrás" del teléfono cierra la hoja abierta en lugar de salir de la pantalla.
// Cada hoja agrega una entrada al historial (conservando idx/key/usr de React Router, así el router no
// ve un cambio de ruta) y la quita al cerrarse con su botón. El retiro se difiere un tick y, si antes de
// que corra se monta otra hoja sobre esa entrada pendiente (StrictMode en desarrollo: monta, limpia y
// vuelve a montar), la nueva reutiliza la entrada con replaceState en lugar de apilar otra, y el retiro
// pendiente se cancela. Así no queda ninguna entrada huérfana.
export function useBackToClose(enabled, onClose) {
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    if (!enabled) return undefined
    counter += 1
    const id = `pos-sheet-${counter}`
    const current = window.history.state
    if (current?.posSheet && pendingRemoval.has(current.posSheet)) {
      pendingRemoval.delete(current.posSheet)
      window.history.replaceState({ ...current, posSheet: id }, '')
    } else {
      window.history.pushState({ ...current, posSheet: id }, '')
    }
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
      pendingRemoval.add(id)
      setTimeout(() => {
        if (!pendingRemoval.delete(id)) return
        if (window.history.state?.posSheet === id) window.history.back()
      }, 0)
    }
  }, [enabled])
}
