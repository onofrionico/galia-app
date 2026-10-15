import { describe, expect, it } from 'vitest'
import { centeredScrollLeft } from './chipScroll'

describe('centeredScrollLeft', () => {
  it('centra el chip dentro de la barra', () => {
    // Barra de 300 px, chip de 100 px que empieza en 500: centro en 550 → scroll 400.
    expect(centeredScrollLeft({ chipLeft: 500, chipWidth: 100, navWidth: 300, scrollWidth: 1200 })).toBe(400)
  })

  it('no se pasa del principio ni del final de la barra', () => {
    expect(centeredScrollLeft({ chipLeft: 10, chipWidth: 80, navWidth: 300, scrollWidth: 1200 })).toBe(0)
    expect(centeredScrollLeft({ chipLeft: 1150, chipWidth: 50, navWidth: 300, scrollWidth: 1200 })).toBe(900)
  })

  it('si todo entra en la barra no scrollea', () => {
    expect(centeredScrollLeft({ chipLeft: 200, chipWidth: 60, navWidth: 400, scrollWidth: 400 })).toBe(0)
  })
})
