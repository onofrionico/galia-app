import { describe, expect, it } from 'vitest'
import { groupHint, linePreview, selectionError, toggleOption } from './modifiers'

const leche = { id: 1, name: 'Leche', min_select: 1, max_select: 1, options: [{ id: 11, price_delta: 0 }, { id: 12, price_delta: 500 }] }
const extras = { id: 2, name: 'Extras', min_select: 0, max_select: 2, options: [{ id: 21, price_delta: 600 }, { id: 22, price_delta: 900 }, { id: 23, price_delta: 0 }] }

describe('toggleOption', () => {
  it('con máximo 1 reemplaza la opción del grupo', () => {
    expect(toggleOption(leche, [11, 21], 12)).toEqual([21, 12])
  })
  it('quita si ya estaba', () => {
    expect(toggleOption(extras, [21], 21)).toEqual([])
  })
  it('no supera el máximo', () => {
    expect(toggleOption(extras, [21, 22], 23)).toEqual([21, 22])
  })
})

describe('validación y precio', () => {
  it('exige el mínimo de cada grupo', () => {
    expect(selectionError([leche, extras], [])).toBe('Elegí al menos 1 en "Leche"')
    expect(selectionError([leche, extras], [12])).toBeNull()
  })
  it('vista previa del renglón', () => {
    expect(linePreview({ price: 3500 }, [leche, extras], [12, 21], 2)).toBe(9200)
  })
  it('explica la regla del grupo', () => {
    expect(groupHint(leche)).toBe('elegí 1, obligatorio')
    expect(groupHint({ min_select: 1, max_select: 3 })).toBe('elegí de 1 a 3, obligatorio')
    expect(groupHint(extras)).toBe('opcional, hasta 2')
  })
})
