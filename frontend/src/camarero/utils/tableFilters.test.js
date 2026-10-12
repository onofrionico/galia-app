import { describe, expect, it } from 'vitest'
import { filterTables, hasPending, isDimmed, isMine, waiterLabel } from './tableFilters'

const sale = (id, waiterId, pending = 0, status = 'open') => ({
  id, status, waiter: waiterId ? { id: waiterId, name: `Mozo ${waiterId}` } : null, pending_count: pending,
})
const free = { id: 1, label: 'Mesa 1', sales: [] }
const mine = { id: 2, label: 'Mesa 2', sales: [sale(10, 7, 1)] }
const other = { id: 3, label: 'Mesa 3', sales: [sale(11, 8)] }
const shared = { id: 4, label: 'Mesa 4', sales: [sale(12, 8), sale(13, 7, 0, 'billing')] }
const tables = [free, mine, other, shared]

describe('tableFilters', () => {
  it('isMine compara el mozo de cualquier cuenta, aunque el id venga como texto', () => {
    expect(isMine(mine, 7)).toBe(true)
    expect(isMine(mine, '7')).toBe(true)
    expect(isMine(shared, 7)).toBe(true)
    expect(isMine(other, 7)).toBe(false)
    expect(isMine(free, 7)).toBe(false)
    expect(isMine(other, undefined)).toBe(false)
  })

  it('filterTables: "Todas" muestra todo; "Mías" las propias más las libres', () => {
    expect(filterTables(tables, 'all', 7)).toEqual(tables)
    expect(filterTables(tables, 'mine', 7).map((t) => t.id)).toEqual([1, 2, 4])
  })

  it('isDimmed atenúa en el plano solo las ocupadas ajenas con el filtro "Mías"', () => {
    expect(isDimmed(other, 'mine', 7)).toBe(true)
    expect(isDimmed(free, 'mine', 7)).toBe(false)
    expect(isDimmed(mine, 'mine', 7)).toBe(false)
    expect(isDimmed(other, 'all', 7)).toBe(false)
  })

  it('hasPending detecta ítems sin confirmar en cualquier cuenta', () => {
    expect(hasPending(mine)).toBe(true)
    expect(hasPending(shared)).toBe(false)
    expect(hasPending(free)).toBe(false)
    expect(hasPending({ sales: [{ id: 1 }] })).toBe(false)
  })

  it('waiterLabel muestra "Vos" para el usuario actual', () => {
    expect(waiterLabel(mine, 7)).toBe('Vos')
    expect(waiterLabel(other, 7)).toBe('Mozo 8')
    expect(waiterLabel(free, 7)).toBe(null)
  })
})
