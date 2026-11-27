import { describe, expect, it } from 'vitest'
import { argentinaDate, dateTimeLabel, cashStatusLabel, closeValidation, countDifference, differenceTone, argentinaLocalInput, localInputLabel, openedBeforeToday, toArgentinaIso } from './cashMath'

const methods = [
  { payment_method_id: 1, method_name: 'Efectivo', kind: 'cash', expected: 1900 },
  { payment_method_id: 2, method_name: 'Débito', kind: 'card', expected: 900 },
]

describe('countDifference', () => {
  it('resta lo esperado a lo contado y respeta el formato argentino', () => {
    expect(countDifference(1900, '1.850')).toBe(-50)
    expect(countDifference(900, '900,5')).toBe(0.5)
    expect(countDifference(900, '')).toBe(null)
    expect(countDifference(900, 'abc')).toBe(null)
  })
})

describe('differenceTone', () => {
  it('clasifica la diferencia', () => {
    expect(differenceTone(-1)).toBe('missing')
    expect(differenceTone(2)).toBe('over')
    expect(differenceTone(0)).toBe('even')
    expect(differenceTone(null)).toBe(null)
  })
})

describe('closeValidation', () => {
  it('exige el efectivo', () => {
    const result = closeValidation(methods, { 2: '900' }, '')
    expect(result.ok).toBe(false)
    expect(result.error).toBe('Cargá lo contado en efectivo')
  })

  it('toma lo esperado en los medios vacíos (no los envía: el backend usa su esperado)', () => {
    const result = closeValidation(methods, { 1: '1900' }, '')
    expect(result).toEqual({ ok: true, error: null, counts: [
      { payment_method_id: 1, counted: 1900 },
    ] })
  })

  it('exige nota si hay diferencia', () => {
    expect(closeValidation(methods, { 1: '1850' }, '  ').error).toBe('Explicá la diferencia en la nota')
    expect(closeValidation(methods, { 1: '1850' }, 'Faltante').ok).toBe(true)
  })

  it('rechaza valores inválidos o negativos', () => {
    expect(closeValidation(methods, { 1: '1900', 2: 'x' }, '').error).toBe('Revisá lo contado en Débito')
    expect(closeValidation(methods, { 1: '-5' }, 'n').error).toBe('Revisá lo contado en Efectivo')
  })
})

describe('cashStatusLabel', () => {
  it('describe el estado de la caja', () => {
    const fmt = () => '09:02'
    expect(cashStatusLabel({ open_session: { opened_at: '2026-10-13T12:02:00' } }, fmt)).toBe('Caja abierta · desde 09:02')
    expect(cashStatusLabel({ open_session: null }, fmt)).toBe('Caja cerrada')
    expect(cashStatusLabel(null, fmt)).toBe('Sin caja configurada')
  })
})

describe('apertura con hora anterior', () => {
  it('agrega el offset de Argentina a la hora del datetime-local', () => {
    expect(toArgentinaIso('2026-11-26T08:00')).toBe('2026-11-26T08:00:00-03:00')
    expect(toArgentinaIso('')).toBe(null)
  })
  it('lleva una hora UTC del backend al día de Argentina', () => {
    expect(argentinaDate('2026-11-27T02:30:00')).toBe('2026-11-26')
    expect(argentinaDate('2026-11-27T03:30:00')).toBe('2026-11-27')
  })
  it('dice si la caja se abrió un día anterior a hoy', () => {
    expect(openedBeforeToday({ opened_at: '2026-11-26T11:00:00' }, '2026-11-27')).toBe(true)
    expect(openedBeforeToday({ opened_at: '2026-11-27T11:00:00' }, '2026-11-27')).toBe(false)
  })
})

describe('argentinaLocalInput', () => {
  it('formatea un instante como valor de datetime-local en hora de Argentina', () => {
    expect(argentinaLocalInput(new Date('2026-11-27T14:05:00Z'))).toBe('2026-11-27T11:05')
  })
  it('lleva el valor a dd/mm HH:MM para el aviso', () => {
    expect(localInputLabel('2026-11-26T08:00')).toBe('26/11 08:00')
  })
})

describe('dateTimeLabel', () => {
  it('muestra la hora del backend en dd/mm HH:MM de Argentina', () => {
    expect(dateTimeLabel('2026-11-26T11:00:00')).toBe('26/11 08:00')
  })
})
