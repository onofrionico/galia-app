import { useEffect, useState } from 'react'
import QRCode from 'qrcode'
import { formatMoney } from '../../pos/utils/money'
import { chunk, formatExpiry } from './voucherUtils'

const PER_PAGE = 8

// Oculta el resto de la app al imprimir y deja solo la hoja de vouchers en A4.
const PRINT_CSS = `
@media print {
  @page { size: A4; margin: 8mm; }
  body * { visibility: hidden; }
  #voucher-print-area, #voucher-print-area * { visibility: visible; }
  #voucher-print-area { position: absolute; left: 0; top: 0; width: 100%; }
  .voucher-page { break-after: page; }
  .voucher-page:last-child { break-after: auto; }
}`

function VoucherCard({ batch, voucher, qr }) {
  return (
    <div className="flex h-[68mm] overflow-hidden border border-dashed border-gray-400 bg-galia-cream p-3 text-galia-plum">
      <div className="flex min-w-0 flex-1 flex-col justify-between pr-2">
        <div>
          <img src="/brand/logo.png" alt="Galia Café" className="h-9 w-auto" />
          <p className="mt-1 text-[10px] font-semibold uppercase tracking-widest text-galia-plum-light">Voucher de descuento</p>
          <p className="font-display text-3xl font-bold leading-tight">{formatMoney(batch.amount)}</p>
          <p className="truncate text-xs font-medium">{batch.name}</p>
        </div>
        <div>
          {batch.terms && <p className="line-clamp-3 text-[9px] leading-tight text-gray-700">{batch.terms}</p>}
          <p className="mt-1 text-[10px] font-semibold">Válido hasta el {formatExpiry(batch.expires_at)}</p>
        </div>
      </div>
      <div className="flex w-[34mm] flex-col items-center justify-between">
        {qr ? <img src={qr} alt="" className="h-[30mm] w-[30mm]" /> : <div className="h-[30mm] w-[30mm]" />}
        <p className="font-mono text-[11px] font-bold tracking-wider">{voucher.code}</p>
        <p className="text-center text-[8px] leading-tight text-gray-600">Entregá este código en caja. Se canjea una sola vez.</p>
      </div>
    </div>
  )
}

// Hoja imprimible: 8 vouchers por A4 (2 × 4), solo los disponibles. `onReady` avisa cuando los QR están listos.
export default function PrintSheet({ batch, onReady }) {
  const available = batch.vouchers.filter((v) => v.status === 'available')
  const [qrs, setQrs] = useState({})

  useEffect(() => {
    let cancelled = false
    Promise.all(available.map(async (v) => [v.id, await QRCode.toDataURL(v.code_raw, { margin: 0, width: 220 })]))
      .then((pairs) => {
        if (cancelled) return
        setQrs(Object.fromEntries(pairs))
        onReady?.()
      })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [batch.id, available.length])

  if (available.length === 0) return <p className="text-sm text-gray-500">No hay vouchers disponibles para imprimir.</p>

  return (
    <div id="voucher-print-area" className="bg-white">
      <style>{PRINT_CSS}</style>
      {chunk(available, PER_PAGE).map((page, index) => (
        <div key={index} className="voucher-page grid grid-cols-2 gap-0">
          {page.map((voucher) => <VoucherCard key={voucher.id} batch={batch} voucher={voucher} qr={qrs[voucher.id]} />)}
        </div>
      ))}
    </div>
  )
}
