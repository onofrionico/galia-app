import { describe, it, expect } from 'vitest'
import { formatPrice, formatVariant, instagramHandle } from './format'

describe('formatPrice', () => {
  it('usa separador de miles argentino', () => {
    expect(formatPrice(6900)).toBe('$6.900')
    expect(formatPrice(12600.5)).toBe('$12.600,5')
  })
})

describe('formatVariant', () => {
  it('incluye la etiqueta si existe', () => {
    expect(formatVariant({ label: 'Porción', price: 11200 })).toBe('Porción $11.200')
    expect(formatVariant({ label: null, price: 4400 })).toBe('$4.400')
  })
})

describe('instagramHandle', () => {
  it('normaliza arroba, espacios y URLs', () => {
    expect(instagramHandle(' @galia.cafe ')).toBe('galia.cafe')
    expect(instagramHandle('https://www.instagram.com/galia.cafe/?hl=es')).toBe('galia.cafe')
    expect(instagramHandle('instagram.com/@galia.cafe')).toBe('galia.cafe')
    expect(instagramHandle(undefined)).toBe('')
    expect(instagramHandle(42)).toBe('')
  })
})
