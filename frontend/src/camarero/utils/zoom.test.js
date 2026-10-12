import { describe, expect, it } from 'vitest'
import { MAX_ZOOM, MIN_ZOOM, clampZoom, pinchZoom, stepZoom } from './zoom'

describe('zoom', () => {
  it('clampZoom limita entre 1× y 3× y corrige valores inválidos', () => {
    expect(clampZoom(0.5)).toBe(MIN_ZOOM)
    expect(clampZoom(4)).toBe(MAX_ZOOM)
    expect(clampZoom(1.7)).toBe(1.7)
    expect(clampZoom(Number.NaN)).toBe(MIN_ZOOM)
  })

  it('stepZoom avanza de a 0,5 y redondea al paso', () => {
    expect(stepZoom(1, 1)).toBe(1.5)
    expect(stepZoom(1.7, 1)).toBe(2)
    expect(stepZoom(1, -1)).toBe(1)
    expect(stepZoom(3, 1)).toBe(3)
  })

  it('pinchZoom escala según la distancia entre los dedos', () => {
    expect(pinchZoom(1, 100, 200)).toBe(2)
    expect(pinchZoom(2, 100, 50)).toBe(1)
    expect(pinchZoom(2, 100, 1000)).toBe(3)
    expect(pinchZoom(1.5, 0, 50)).toBe(1.5)
  })
})
