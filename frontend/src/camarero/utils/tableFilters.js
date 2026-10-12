import { tableStatus } from '../../pos/utils/floor'

const sameId = (a, b) => a != null && b != null && Number(a) === Number(b)

// La mesa es "mía" si alguna de sus cuentas tiene como mozo al usuario actual.
export const isMine = (table, userId) => (table.sales ?? []).some((s) => sameId(s.waiter?.id, userId))

export const hasPending = (table) => (table.sales ?? []).some((s) => (s.pending_count ?? 0) > 0)

// "Mías": las propias más las libres (para poder abrir una mesa nueva).
export function filterTables(tables, filter, userId) {
  if (filter !== 'mine') return tables
  return tables.filter((t) => tableStatus(t) === 'free' || isMine(t, userId))
}

// En el plano no se ocultan mesas: con "Mías" se atenúan las ocupadas ajenas.
export const isDimmed = (table, filter, userId) =>
  filter === 'mine' && tableStatus(table) !== 'free' && !isMine(table, userId)

export function waiterLabel(table, userId) {
  const waiter = table.sales?.[0]?.waiter
  if (!waiter) return null
  return sameId(waiter.id, userId) ? 'Vos' : waiter.name
}
