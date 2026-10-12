import { describe, expect, it } from 'vitest'
import { newRequestId } from './ids'

describe('newRequestId', () => {
  it('genera ids distintos de hasta 64 caracteres', () => {
    const a = newRequestId()
    const b = newRequestId()
    expect(a).not.toBe(b)
    expect(a.length).toBeLessThanOrEqual(64)
  })
})
