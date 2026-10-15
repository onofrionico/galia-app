import { describe, expect, it } from 'vitest'
import { categoryPayload } from './categoryPayload'

describe('categoryPayload', () => {
  const form = { name: 'Platos', description: '', color: '#000', icon: '🍽', station_id: '' }

  it('al crear manda la estación elegida o null', () => {
    expect(categoryPayload({ ...form, station_id: '3' }, null).station_id).toBe(3)
    expect(categoryPayload(form, null).station_id).toBeNull()
  })

  it('al editar no toca la estación si no se cambió (aunque las estaciones no hayan cargado)', () => {
    const original = { id: 1, station_id: 4 }
    expect('station_id' in categoryPayload(form, original, { stationTouched: false })).toBe(false)
    expect(categoryPayload({ ...form, station_id: '' }, original, { stationTouched: true }).station_id).toBeNull()
    expect(categoryPayload({ ...form, station_id: '2' }, original, { stationTouched: true }).station_id).toBe(2)
  })
})
