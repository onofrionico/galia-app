import { describe, it, expect } from 'vitest'
import { GALIA_COLORS, contrastRatio } from './galia-tokens.js'
import preset from './galia-preset.js'

describe('paleta oficial de Galia', () => {
  it('usa los valores exactos del sistema de diseño', () => {
    expect(GALIA_COLORS).toEqual({
      plum: '#673b4c',
      terracotta: '#dd8c76',
      lime: '#cbd159',
      cream: '#edece4',
      sand100: '#e1ded0',
      sand200: '#d1cdba',
      white: '#ffffff',
    })
  })
})

describe('contraste del texto ciruela', () => {
  const { plum, cream, white, lime, sand100, terracotta } = GALIA_COLORS

  it('sobre crema es >= 7.5', () => expect(contrastRatio(plum, cream)).toBeGreaterThanOrEqual(7.5))
  it('sobre blanco es >= 9', () => expect(contrastRatio(plum, white)).toBeGreaterThanOrEqual(9))
  it('sobre lima es >= 5.5', () => expect(contrastRatio(plum, lime)).toBeGreaterThanOrEqual(5.5))
  it('sobre arena clara es >= 6.5', () => expect(contrastRatio(plum, sand100)).toBeGreaterThanOrEqual(6.5))
  it('terracota sobre crema NO alcanza para texto (< 3)', () =>
    expect(contrastRatio(terracotta, cream)).toBeLessThan(3))
})

describe('preset de Tailwind', () => {
  const ext = preset.theme.extend

  it('ancla la escala plum (blue y rose) en la ciruela oficial', () => {
    expect(ext.colors.blue[700]).toBe(GALIA_COLORS.plum)
    expect(ext.colors.rose[700]).toBe(GALIA_COLORS.plum)
  })

  it('ancla la escala terracota (purple) en el terracota oficial', () => {
    expect(ext.colors.purple[400]).toBe(GALIA_COLORS.terracotta)
  })

  it('expone los colores galia.*', () => {
    expect(ext.colors.galia.plum).toBe(GALIA_COLORS.plum)
    expect(ext.colors.galia.lime).toBe(GALIA_COLORS.lime)
    expect(ext.colors.galia.cream).toBe(GALIA_COLORS.cream)
    expect(ext.colors.galia.coral).toBe(GALIA_COLORS.terracotta)
  })

  it('usa Poppins para texto y Anton para títulos', () => {
    expect(ext.fontFamily.sans[0]).toBe('Poppins')
    expect(ext.fontFamily.display[0]).toBe('Anton')
  })

  it('define los radios del sistema', () => {
    expect(ext.borderRadius['galia-lg']).toBe('24px')
    expect(ext.borderRadius['galia-sm']).toBe('6px')
    expect(ext.borderRadius.pill).toBe('999px')
  })

  it('registra las clases galia-* como componentes', () => {
    const registered = {}
    const api = { addComponents: (c) => Object.assign(registered, c) }
    preset.plugins.forEach((p) => p(api))
    for (const cls of ['.galia-price', '.galia-label', '.galia-banner', '.galia-sticker', '.galia-divider', '.galia-card']) {
      expect(registered).toHaveProperty([cls])
    }
  })
})
