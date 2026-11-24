import { describe, it, expect } from 'vitest'
import GALIA from './colors'
import { GALIA_COLORS } from '../../../shared/galia-tokens.js'

describe('constants/colors', () => {
  it('marron es la ciruela oficial', () => expect(GALIA.marron).toBe(GALIA_COLORS.plum))
  it('amarillo es la lima oficial', () => expect(GALIA.amarillo).toBe(GALIA_COLORS.lime))
  it('crema es la crema oficial', () => expect(GALIA.crema).toBe(GALIA_COLORS.cream))
  it('blanco es blanco', () => expect(GALIA.blanco).toBe(GALIA_COLORS.white))
})
