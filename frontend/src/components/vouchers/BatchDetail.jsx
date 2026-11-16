import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Printer } from 'lucide-react'
import voucherService from '../../services/voucherService'
import { formatMoney } from '../../pos/utils/money'
import { ErrorText, button, dateTime, input } from '../loyalty/shared'
import PrintSheet from './PrintSheet'
import { STATUS_LABEL, availableKey, formatExpiry, useVoucherMutation, voucherKeys } from './voucherUtils'

const STATUS_STYLE = {
  available: 'bg-green-100 text-green-800',
  in_use: 'bg-amber-100 text-amber-800',
  redeemed: 'bg-gray-200 text-gray-700',
  expired: 'bg-red-100 text-red-800',
  voided: 'bg-red-100 text-red-800',
}

function Counter({ label, value }) {
  return <div className="rounded-lg border p-2 text-center"><p className="text-xl font-bold">{value}</p><p className="text-xs text-gray-500">{label}</p></div>
}

export default function BatchDetail({ batchId, onBack }) {
  const { data: batch } = useQuery({ queryKey: voucherKeys.batch(batchId), queryFn: () => voucherService.getBatch(batchId) })
  const [newExpiry, setNewExpiry] = useState('')
  const [voiding, setVoiding] = useState(null)
  const [reason, setReason] = useState('')
  const [preview, setPreview] = useState(false)
  const [readyKey, setReadyKey] = useState(null)
  const [wantPrint, setWantPrint] = useState(false)
  const extend = useVoucherMutation(() => voucherService.extendExpiry(batchId, newExpiry))
  const voidVoucher = useVoucherMutation(({ id, text }) => voucherService.voidVoucher(id, text))
  const key = batch ? availableKey(batch) : ''

  // Imprime cuando el usuario lo pidió y los QR de los vouchers disponibles de ahora ya están listos.
  useEffect(() => {
    if (wantPrint && key && readyKey === key) {
      setWantPrint(false)
      window.print()
    }
  }, [wantPrint, readyKey, key])

  if (!batch) return <p className="text-sm text-gray-500">Cargando…</p>

  const print = () => { setPreview(true); setWantPrint(true) }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" className={button()} onClick={onBack}><ArrowLeft size={16} /> Tandas</button>
        <h2 className="text-lg font-semibold">{batch.name}</h2>
        <span className="text-sm text-gray-600">{formatMoney(batch.amount)} · vence el {formatExpiry(batch.expires_at)}
          {batch.min_sale_amount ? ` · mínimo ${formatMoney(batch.min_sale_amount)}` : ''}</span>
        <button type="button" className={`${button(true)} ml-auto`} onClick={print} disabled={!key}
          title={key ? undefined : 'No hay vouchers disponibles para imprimir'}><Printer size={16} /> Imprimir</button>
      </div>

      <div className="grid grid-cols-3 gap-2 md:grid-cols-7">
        <Counter label="Emitidos" value={batch.issued} />
        <Counter label="Disponibles" value={batch.available} />
        <Counter label="En uso" value={batch.in_use} />
        <Counter label="Canjeados" value={batch.redeemed} />
        <Counter label="Vencidos" value={batch.expired} />
        <Counter label="Anulados" value={batch.voided} />
        <Counter label="Descuento dado" value={formatMoney(batch.discount_total)} />
      </div>

      <form className="flex flex-wrap items-center gap-2"
        onSubmit={(e) => { e.preventDefault(); extend.mutate(undefined, { onSuccess: () => setNewExpiry('') }) }}>
        <label className="text-sm">Extender vencimiento hasta</label>
        <input className={input} type="date" value={newExpiry} onChange={(e) => setNewExpiry(e.target.value)} required />
        <button type="submit" className={button()} disabled={extend.isPending}>Extender</button>
        <ErrorText>{extend.errorText}</ErrorText>
      </form>

      <table className="w-full text-sm">
        <thead><tr className="text-left text-gray-500"><th className="py-1">Código</th><th>Estado</th><th>Venta</th><th>Fecha</th><th /></tr></thead>
        <tbody>
          {batch.vouchers.map((v) => (
            <tr key={v.id} className="border-t">
              <td className="py-2 font-mono">{v.code}</td>
              <td><span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[v.status]}`}>{STATUS_LABEL[v.status]}</span>
                {v.void_reason ? <span className="ml-2 text-xs text-gray-500">{v.void_reason}</span> : null}</td>
              <td>{v.sale_number ? `#${v.sale_number} · ${formatExpiry(v.sale_date)}` : '—'}</td>
              <td>{dateTime(v.redeemed_at)}</td>
              <td className="text-right">
                {['available', 'expired'].includes(v.status) && voiding !== v.id && (
                  <button type="button" className="text-red-700 underline" onClick={() => { setVoiding(v.id); setReason('') }}>Anular</button>
                )}
                {voiding === v.id && (
                  <form className="inline-flex gap-1"
                    onSubmit={(e) => { e.preventDefault(); voidVoucher.mutate({ id: v.id, text: reason }, { onSuccess: () => setVoiding(null) }) }}>
                    <input className={`${input} w-40`} placeholder="Motivo" value={reason} onChange={(e) => setReason(e.target.value)} required autoFocus />
                    <button type="submit" className={button(true)} disabled={voidVoucher.isPending}>Anular</button>
                    <button type="button" className={button()} onClick={() => setVoiding(null)}>No</button>
                  </form>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <ErrorText>{voidVoucher.errorText}</ErrorText>

      {preview && (
        <section>
          <h3 className="mb-2 font-semibold">Vista previa de impresión</h3>
          <div className="overflow-x-auto rounded-lg border bg-gray-100 p-2">
            <div className="mx-auto w-[194mm]"><PrintSheet batch={batch} onReady={setReadyKey} /></div>
          </div>
        </section>
      )}
    </div>
  )
}
