import { candidateLegend, isFudoLocked, syncSummary, variantFudoStatus } from './fudoLock'

describe('isFudoLocked', () => {
  it('is true only for listed fields', () => {
    const product = { fudo_locked_fields: ['name', 'category_id'] }
    expect(isFudoLocked(product, 'name')).toBe(true)
    expect(isFudoLocked(product, 'description')).toBe(false)
    expect(isFudoLocked(null, 'name')).toBe(false)
    expect(isFudoLocked({}, 'name')).toBe(false)
  })
})

describe('variantFudoStatus', () => {
  it('returns null for manual variants and ok by default for linked ones', () => {
    expect(variantFudoStatus({ fudo_product_id: null })).toBe(null)
    expect(variantFudoStatus({ fudo_product_id: '1', fudo_status: null })).toBe('ok')
    expect(variantFudoStatus({ fudo_product_id: '1', fudo_status: 'missing' })).toBe('missing')
  })
})

describe('syncSummary', () => {
  it('summarizes the catalog stats', () => {
    expect(syncSummary({ catalog: { variants_updated: 12, products_created: 3, alerts: 1 } }))
      .toBe('Fudo sincronizado: 12 variantes actualizadas · 3 productos nuevos · 1 alerta')
    expect(syncSummary({ catalog: { variants_updated: 0, products_created: 0, alerts: 0 } }))
      .toBe('Fudo sincronizado: 0 variantes actualizadas · 0 productos nuevos')
    expect(syncSummary({ catalog: { variants_updated: 1, products_created: 1, alerts: 2 } }))
      .toBe('Fudo sincronizado: 1 variante actualizada · 1 producto nuevo · 2 alertas')
  })
})

describe('candidateLegend', () => {
  it('explains where the candidate is', () => {
    expect(candidateLegend({ product_id: 5, product_name: 'Café' }, 5)).toBe('ya en este producto')
    expect(candidateLegend({ product_id: 7, product_name: 'Café grande' }, 5)).toBe('se moverá desde «Café grande»')
    expect(candidateLegend({ product_id: null, is_active: false }, 5)).toBe('inactivo en Fudo')
    expect(candidateLegend({ product_id: null, is_active: true }, 5)).toBe(null)
  })
})
