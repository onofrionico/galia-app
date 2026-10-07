import { describe, it, expect } from 'vitest'
import { normalize } from './text'

describe('normalize', () => {
  it('quita tildes y pasa a minúsculas', () => {
    expect(normalize('Café con LECHE Ñandú')).toBe('cafe con leche nandu')
  })

  it('tolera null', () => {
    expect(normalize(null)).toBe('')
  })
})
