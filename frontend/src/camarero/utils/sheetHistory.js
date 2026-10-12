// Cómo volver a las mesas desde la venta.
// - Si se llegó desde las mesas, se vuelve atrás en el historial (no se apila otra entrada de mesas); si
//   hay una hoja cerrándose encima, primero se espera a que retire su entrada.
// - Si no (link directo, recarga, login), se navega a las mesas; reemplazando la entrada de la hoja si la hay.
export function backToTablesAction({ fromTables, sheetOnTop }) {
  if (fromTables) return { kind: 'back', afterSheet: sheetOnTop }
  return { kind: 'tables', replace: sheetOnTop }
}

// Corre `onBack` después de que la hoja que se está cerrando retire su entrada del historial (su
// history.back() diferido de useBackToClose). Si no hay hoja encima, corre enseguida. Si el popstate no
// llega a tiempo, corre `onTimeout` para que nunca quede trabado.
export function afterSheetBack(onBack, onTimeout = onBack, { win = window, timeout = 300 } = {}) {
  if (!win.history.state?.posSheet) {
    onBack()
    return
  }
  let done = false
  const finish = (callback) => {
    if (done) return
    done = true
    win.removeEventListener('popstate', onPop)
    clearTimeout(timer)
    callback()
  }
  const onPop = () => finish(onBack)
  const timer = setTimeout(() => finish(onTimeout), timeout)
  win.addEventListener('popstate', onPop)
}
