import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { afterSheetBack, backToTablesAction } from './sheetHistory'

describe('backToTablesAction', () => {
  it('desde las mesas vuelve atrás; si hay una hoja encima, después de que se retire', () => {
    expect(backToTablesAction({ fromTables: true, sheetOnTop: false })).toEqual({ kind: 'back', afterSheet: false })
    expect(backToTablesAction({ fromTables: true, sheetOnTop: true })).toEqual({ kind: 'back', afterSheet: true })
  })

  it('sin origen en las mesas navega a ellas, reemplazando la entrada de la hoja si la hay', () => {
    expect(backToTablesAction({ fromTables: false, sheetOnTop: false })).toEqual({ kind: 'tables', replace: false })
    expect(backToTablesAction({ fromTables: false, sheetOnTop: true })).toEqual({ kind: 'tables', replace: true })
  })
})

describe('afterSheetBack', () => {
  const fakeWindow = (state) => {
    const target = new EventTarget()
    target.history = { state }
    return target
  }

  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('sin hoja encima corre enseguida', () => {
    const onBack = vi.fn()
    afterSheetBack(onBack, vi.fn(), { win: fakeWindow({ idx: 1 }) })
    expect(onBack).toHaveBeenCalledTimes(1)
  })

  it('con hoja encima espera el popstate y corre una sola vez', () => {
    const win = fakeWindow({ posSheet: 'pos-sheet-1' })
    const onBack = vi.fn()
    const onTimeout = vi.fn()
    afterSheetBack(onBack, onTimeout, { win })
    expect(onBack).not.toHaveBeenCalled()
    win.dispatchEvent(new Event('popstate'))
    win.dispatchEvent(new Event('popstate'))
    vi.advanceTimersByTime(1000)
    expect(onBack).toHaveBeenCalledTimes(1)
    expect(onTimeout).not.toHaveBeenCalled()
  })

  it('si el popstate no llega, corre el respaldo', () => {
    const win = fakeWindow({ posSheet: 'pos-sheet-1' })
    const onBack = vi.fn()
    const onTimeout = vi.fn()
    afterSheetBack(onBack, onTimeout, { win, timeout: 300 })
    vi.advanceTimersByTime(299)
    expect(onTimeout).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    win.dispatchEvent(new Event('popstate'))
    expect(onTimeout).toHaveBeenCalledTimes(1)
    expect(onBack).not.toHaveBeenCalled()
  })
})
