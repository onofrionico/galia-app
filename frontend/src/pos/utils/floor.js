import { round2 } from './money'

// Las mesas guardan posición y tamaño en unidades lógicas: el lienzo mide 100 de ancho.
export const LOGICAL_WIDTH = 100
export const MIN_CANVAS_HEIGHT = 60
export const GRID = 1
export const MIN_SIZE = 4

export function tableStatus(table) {
  const sales = table.sales ?? []
  if (sales.length === 0) return 'free'
  return sales.every((s) => s.status === 'billing') ? 'billing' : 'open'
}

export function tableSummary(table) {
  const sales = table.sales ?? []
  const openedAt = sales.map((s) => s.opened_at).filter(Boolean).sort()[0] ?? null
  return {
    count: sales.length,
    total: round2(sales.reduce((sum, s) => sum + Number(s.total || 0), 0)),
    waiter: sales[0]?.waiter?.name ?? null,
    openedAt,
  }
}

export const snap = (value) => Math.max(0, Math.round(value / GRID) * GRID)

export function clampPosition({ pos_x, pos_y, width }) {
  return { pos_x: Math.min(Math.max(0, pos_x), LOGICAL_WIDTH - width), pos_y: Math.max(0, pos_y) }
}

export function clampSize({ pos_x, width, height }) {
  return { width: Math.min(Math.max(MIN_SIZE, width), LOGICAL_WIDTH - pos_x), height: Math.max(MIN_SIZE, height) }
}

export function canvasHeight(tables) {
  return Math.max(MIN_CANVAS_HEIGHT, ...tables.map((t) => t.pos_y + t.height + 4))
}
