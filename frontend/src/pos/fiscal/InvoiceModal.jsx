import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posFiscalApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { DOC_TYPES, IVA_CONDITIONS, customerPayload, previewSummary, validateCustomer } from './invoiceForm'

const EMPTY = { mode: 'anonymous', docType: 'DNI', docNumber: '', name: '', ivaCondition: 'consumidor_final', address: '' }

// Facturar una venta cerrada: consumidor final o con datos (con sugerencias de clientes guardados).
export default function InvoiceModal({ saleId, onClose, onDone }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const { data: preview, isLoading, isError } = useQuery({
    queryKey: posKeys.fiscalPreview(saleId), queryFn: () => posFiscalApi.preview(saleId),
  })
  const set = (patch) => { setForm((f) => ({ ...f, ...patch })); setError('') }

  useEffect(() => {
    const q = form.mode === 'identified' ? (form.docNumber || form.name).trim() : ''
    if (q.length < 2) { setSuggestions([]); return undefined }
    const id = setTimeout(() => { posFiscalApi.customers(q).then(setSuggestions).catch(() => setSuggestions([])) }, 250)
    return () => clearTimeout(id)
  }, [form.mode, form.docNumber, form.name])

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: posKeys.sale(saleId) })
    queryClient.invalidateQueries({ queryKey: posKeys.fiscal })
  }

  const submit = async () => {
    const problem = validateCustomer(form)
    if (problem) return setError(problem)
    setBusy(true)
    try {
      const invoice = await posFiscalApi.issue(saleId, customerPayload(form))
      setResult(invoice)
      refresh()
      if (invoice.print_warning) toast.error(invoice.print_warning)
    } catch (err) {
      if (err?.response?.data?.invoice) refresh()
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
    return undefined
  }

  const verify = async () => {
    setBusy(true)
    try {
      setResult(await posFiscalApi.verify(result.id))
      refresh()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const finish = () => { onDone?.(result); onClose() }
  const title = `Facturar${preview?.environment === 'homologacion' ? ' · PRUEBA' : ''}`

  if (result) {
    const pending = result.status === 'pending'
    return (
      <Modal title={title} onClose={finish} size="sm"
        footer={(
          <div className="grid grid-cols-2 gap-2">
            {pending
              ? <button type="button" className={btn('secondary')} disabled={busy} onClick={verify}>Verificar</button>
              : <span />}
            <button type="button" className={btn('primary')} onClick={finish}>Listo</button>
          </div>
        )}>
        {pending && (
          <p className="rounded-lg bg-amber-50 p-3 text-amber-900">No pudimos confirmar con ARCA. Tocá Verificar en unos segundos.</p>
        )}
        {result.status === 'authorized' && (
          <div className="space-y-1 py-2 text-center">
            <p className="text-lg font-semibold">{result.label}</p>
            <p className="text-sm text-gray-600">CAE {result.cae}</p>
            {!result.print_warning && <p className="text-sm text-gray-600">Se está imprimiendo en caja.</p>}
          </div>
        )}
        {result.status === 'rejected' && <p className="rounded-lg bg-red-50 p-3 text-red-800">{result.error}</p>}
        {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
      </Modal>
    )
  }

  const canIssue = preview?.ready && Number(preview?.amount) > 0 && !preview?.active_invoice && !preview?.pending_invoice
  return (
    <Modal title={title} onClose={onClose} size="md"
      footer={(
        <button type="button" className={btn('primary', 'w-full')} disabled={busy || isLoading || !canIssue} onClick={submit}>
          {busy ? 'Emitiendo…' : 'Emitir factura'}
        </button>
      )}>
      {isLoading && <p className="text-gray-500">Calculando…</p>}
      {isError && <p className="text-red-700">No se pudo preparar la factura.</p>}
      {preview && (
        <div className="space-y-4">
          {!preview.ready && (
            <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">Falta configurar la facturación: {preview.missing.join(', ')}</p>
          )}
          {preview.active_invoice && <p className="text-sm text-gray-700">La venta ya tiene la {preview.active_invoice.label}.</p>}
          {preview.pending_invoice && <p className="text-sm text-amber-900">Hay una factura sin confirmar: verificala desde la venta.</p>}
          <p className="font-medium">{previewSummary(preview)}</p>
          <div className="flex gap-2">
            {[['anonymous', 'Consumidor final'], ['identified', 'Con datos']].map(([mode, label]) => (
              <button key={mode} type="button" onClick={() => set({ mode })}
                className={btn(form.mode === mode ? 'primary' : 'secondary', 'flex-1')}>{label}</button>
            ))}
          </div>
          {form.mode === 'anonymous' && preview.requires_id_from && (
            <p className="text-xs text-gray-500">
              Desde ${Number(preview.requires_id_from).toLocaleString('es-AR')} hay que identificar al cliente.
            </p>
          )}
          {form.mode === 'identified' && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="text-sm">Documento
                <div className="mt-1 flex gap-2">
                  <select value={form.docType} onChange={(e) => set({ docType: e.target.value })} className="rounded border px-2 py-2">
                    {DOC_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                  <input value={form.docNumber} inputMode="numeric" onChange={(e) => set({ docNumber: e.target.value })}
                    className="w-full rounded border px-2 py-2" />
                </div>
              </label>
              <label className="text-sm">Nombre o razón social
                <input value={form.name} onChange={(e) => set({ name: e.target.value })} className="mt-1 w-full rounded border px-2 py-2" />
              </label>
              {suggestions.length > 0 && (
                <ul className="col-span-full divide-y rounded border text-sm">
                  {suggestions.map((c) => (
                    <li key={c.id}>
                      <button type="button" className="w-full px-3 py-2 text-left hover:bg-gray-50"
                        onClick={() => {
                          set({ docType: c.doc_type, docNumber: c.doc_number, name: c.name, ivaCondition: c.iva_condition, address: c.address ?? '' })
                          setSuggestions([])
                        }}>
                        {c.name} · {c.doc_type} {c.doc_number}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <label className="text-sm">Condición frente al IVA
                <select value={form.ivaCondition} onChange={(e) => set({ ivaCondition: e.target.value })} className="mt-1 w-full rounded border px-2 py-2">
                  {IVA_CONDITIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </label>
              <label className="text-sm">Domicilio (opcional)
                <input value={form.address} onChange={(e) => set({ address: e.target.value })} className="mt-1 w-full rounded border px-2 py-2" />
              </label>
            </div>
          )}
          {error && <p className="text-sm text-red-700">{error}</p>}
        </div>
      )}
    </Modal>
  )
}
