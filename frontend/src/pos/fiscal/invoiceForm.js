import { formatMoney } from '../utils/money'

export const DOC_TYPES = [['DNI', 'DNI'], ['CUIT', 'CUIT'], ['CUIL', 'CUIL']]
export const IVA_CONDITIONS = [
  ['consumidor_final', 'Consumidor final'],
  ['monotributo', 'Monotributo'],
  ['responsable_inscripto', 'Responsable inscripto'],
  ['exento', 'Exento'],
]

const digits = (value) => String(value ?? '').replace(/\D/g, '')
const WEIGHTS = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

export function cuitIsValid(value) {
  const d = digits(value)
  if (d.length !== 11) return false
  const remainder = 11 - (WEIGHTS.reduce((sum, w, i) => sum + w * Number(d[i]), 0) % 11)
  const check = remainder === 11 ? 0 : remainder
  return check !== 10 && check === Number(d[10])
}

// Mismas reglas que el backend (receivers.normalize_receiver), para avisar antes de ir a ARCA.
export function validateCustomer(form) {
  if (form.mode === 'anonymous') return null
  const d = digits(form.docNumber)
  if (form.docType === 'DNI' && (d.length < 7 || d.length > 8)) return 'El DNI tiene que tener 7 u 8 dígitos'
  if (form.docType !== 'DNI' && !cuitIsValid(d)) return `El ${form.docType} es inválido`
  if (!String(form.name ?? '').trim()) return 'Indicá el nombre o la razón social'
  if (['monotributo', 'responsable_inscripto'].includes(form.ivaCondition) && form.docType !== 'CUIT') {
    return 'Para esa condición hace falta el CUIT'
  }
  return null
}

export function customerPayload(form) {
  if (form.mode === 'anonymous') return null
  return {
    doc_type: form.docType,
    doc_number: digits(form.docNumber),
    name: String(form.name).trim(),
    iva_condition: form.ivaCondition,
    address: String(form.address ?? '').trim() || null,
  }
}

export function previewSummary(preview) {
  if (!Number(preview.amount)) return 'Todo lo cobrado en esta venta lo factura otro sistema'
  if (preview.detail_mode === 'items') return `Se facturan los ítems · ${formatMoney(preview.amount)}`
  return `Se factura ${formatMoney(preview.amount)} de ${formatMoney(preview.total)} (lo demás lo factura otro sistema)`
}
