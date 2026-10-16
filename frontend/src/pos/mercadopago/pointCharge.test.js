import { describe, expect, it } from 'vitest'
import { elapsedText, isFinal, isWaiting, resultMessage, waitingLabel } from './pointCharge'

describe('pointCharge', () => {
  it('clasifica los estados', () => {
    expect(isWaiting('created')).toBe(true)
    expect(isWaiting('canceling')).toBe(true)
    expect(isFinal('approved')).toBe(true)
    expect(isFinal('processing')).toBe(false)
  })
  it('describe la espera', () => {
    expect(waitingLabel({ status: 'created' })).toBe('Esperando el cobro en el Point…')
    expect(waitingLabel({ status: 'processing' })).toBe('Cobrando en el Point…')
    expect(waitingLabel({ status: 'canceling' })).toBe('Cancelando en el Point…')
  })
  it('arma el mensaje del resultado', () => {
    expect(resultMessage({ status: 'approved', error: null })).toEqual({ tone: 'ok', text: 'Cobro aprobado' })
    expect(resultMessage({ status: 'approved', error: 'Cobrado de más: $10.00, revisalo en Conciliación' }).tone).toBe('warn')
    expect(resultMessage({ status: 'failed', error: 'El pago fue rechazado en el Point: fondos insuficientes' }))
      .toEqual({ tone: 'error', text: 'El pago fue rechazado en el Point: fondos insuficientes' })
    expect(resultMessage({ status: 'expired', error: null }).text).toBe('El cobro venció sin pagarse')
  })
  it('muestra el tiempo transcurrido', () => {
    expect(elapsedText('2026-10-15T12:00:00', new Date('2026-10-15T12:01:05Z'))).toBe('1:05')
  })
})
