import { describe, expect, it } from 'vitest'
import { apiBase } from './api'

describe('apiBase', () => {
  it('usa VITE_API_URL', () => {
    expect(apiBase({ VITE_API_URL: 'https://galia-backend.onrender.com', PROD: true }))
      .toBe('https://galia-backend.onrender.com/api/public/loyalty')
  })
  it('en producción sin VITE_API_URL no hay API configurada', () => {
    expect(apiBase({ PROD: true })).toBe(null)
  })
  it('en desarrollo cae a la ruta relativa', () => {
    expect(apiBase({ PROD: false })).toBe('/api/public/loyalty')
  })
})
