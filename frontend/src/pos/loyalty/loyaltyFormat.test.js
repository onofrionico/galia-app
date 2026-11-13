import { describe, expect, it } from 'vitest'
import { customerChip, missingFor } from './loyaltyFormat'

describe('customerChip', () => {
  it('muestra nombre, saldo y lo que suma la venta', () => {
    expect(customerChip({ full_name: 'Lucía Pérez', balance: 14 }, 2)).toBe('Lucía Pérez · 14 ☕ · +2')
  })
  it('no muestra +0', () => {
    expect(customerChip({ full_name: 'Lucía Pérez', balance: 14 }, 0)).toBe('Lucía Pérez · 14 ☕')
  })
})

describe('missingFor', () => {
  it('cuánto le falta para un premio', () => {
    expect(missingFor(14, 16)).toBe(2)
    expect(missingFor(14, 8)).toBe(0)
  })
})
