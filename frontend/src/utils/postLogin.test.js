import { describe, expect, it } from 'vitest'
import { postLoginPath } from './postLogin'

describe('postLoginPath', () => {
  it('manda al Camarero a quien tiene Camarero sin POS', () => {
    expect(postLoginPath({ modules: [{ name: 'Camarero' }] })).toBe('/camarero')
    expect(postLoginPath({ modules: ['Camarero', 'Cobrar'] })).toBe('/camarero')
  })

  it('deja en el dashboard a admin, caja y al resto', () => {
    expect(postLoginPath({ isAdmin: true, modules: [] })).toBe('/dashboard')
    expect(postLoginPath({ modules: [{ name: 'Camarero' }, { name: 'POS' }] })).toBe('/dashboard')
    expect(postLoginPath({ modules: [{ name: 'MySchedule' }] })).toBe('/dashboard')
    expect(postLoginPath()).toBe('/dashboard')
  })

  it('vuelve a la ruta de origen: primero la del router, después la guardada', () => {
    const waiter = { modules: [{ name: 'Camarero' }] }
    expect(postLoginPath({ ...waiter, from: '/camarero/venta/12', stored: '/camarero' })).toBe('/camarero/venta/12')
    expect(postLoginPath({ ...waiter, stored: '/camarero/venta/7?add=1' })).toBe('/camarero/venta/7?add=1')
  })

  it('ignora rutas de origen inválidas', () => {
    const waiter = { modules: [{ name: 'Camarero' }] }
    expect(postLoginPath({ ...waiter, from: '/login' })).toBe('/camarero')
    expect(postLoginPath({ ...waiter, stored: '/login?x=1' })).toBe('/camarero')
    expect(postLoginPath({ ...waiter, from: '//evil.example' })).toBe('/camarero')
    expect(postLoginPath({ ...waiter, from: 'https://evil.example' })).toBe('/camarero')
    expect(postLoginPath({ ...waiter, from: 42 })).toBe('/camarero')
  })
})
