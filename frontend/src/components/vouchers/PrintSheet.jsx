import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import QRCode from 'qrcode'
import { formatMoney } from '../../pos/utils/money'
import { PRINT_CSS, availableKey, chunk, formatExpiry, printKey } from './voucherUtils'

const PER_PAGE = 8
const LOAD_TIMEOUT_MS = 5000

// Resuelve cuando la imagen terminó de cargar (o falló). No usamos img.decode(): no resuelve dentro de display:none.
function whenLoaded(img) {
  if (img.complete) return Promise.resolve()
  return new Promise((resolve) => {
    img.addEventListener('load', resolve, { once: true })
    img.addEventListener('error', resolve, { once: true })
  })
}

function VoucherCard({ batch, voucher, qr }) {
  return (
    <div className="flex h-[68mm] overflow-hidden border border-dashed border-gray-400 bg-galia-cream p-3 text-galia-plum">
      <div className="flex min-w-0 flex-1 flex-col justify-between pr-2">
        <div className="text-center">
          <img src="/brand/logo.png" alt="Galia Café" className="mx-auto h-24 w-auto" />
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

// Dorso: solo el nombre de Galia Café, grande y centrado, sobre el color de la marca.
function BackCard() {
  return (
    <div className="flex h-[68mm] items-center justify-center overflow-hidden border border-dashed border-gray-400"
      style={{ backgroundColor: '#673B4C', direction: 'ltr' }}>
      <img src="/brand/logo-nombre.png" alt="Galia Café" className="h-full w-full object-contain" />
    </div>
  )
}

// Cada hoja de frentes va seguida de su hoja de dorsos (para imprimir a doble cara). Los dorsos se acomodan de
// derecha a izquierda: al dar vuelta la hoja por el lado largo, cada dorso queda detrás de su frente.
function Pages({ batch, vouchers, qrs, withBack }) {
  return chunk(vouchers, PER_PAGE).flatMap((page, index) => {
    const front = (
      <div key={`front-${index}`} className="voucher-page grid grid-cols-2 gap-0">
        {page.map((voucher) => <VoucherCard key={voucher.id} batch={batch} voucher={voucher} qr={qrs[voucher.id]} />)}
      </div>
    )
    if (!withBack) return [front]
    const back = (
      <div key={`back-${index}`} className="voucher-page grid grid-cols-2 gap-0" style={{ direction: 'rtl' }}>
        {page.map((voucher) => <BackCard key={voucher.id} />)}
      </div>
    )
    return [front, back]
  })
}

// Hoja imprimible: 8 vouchers por A4 (2 × 4), solo los disponibles. Se muestra una vista previa en pantalla y
// una copia en un portal bajo <body> que es la única que sale en papel. `onReady(key)` avisa cuando los QR y las
// imágenes están listos para el conjunto de vouchers `key` (ver `availableKey`).
export default function PrintSheet({ batch, onReady, withBack = true }) {
  const available = batch.vouchers.filter((v) => v.status === 'available')
  const key = availableKey(batch)
  const readyKey = printKey(batch, withBack)
  const [qrs, setQrs] = useState({})

  useEffect(() => {
    let cancelled = false
    setQrs({})
    Promise.all(available.map(async (v) => [v.id, await QRCode.toDataURL(v.code_raw, { margin: 0, width: 220 })]))
      .then((pairs) => { if (!cancelled) setQrs(Object.fromEntries(pairs)) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  // Cuando todos los QR están en el DOM, espera a que las imágenes se decodifiquen antes de avisar.
  useEffect(() => {
    if (available.length === 0 || !available.every((v) => qrs[v.id])) return undefined
    let cancelled = false
    const images = [...document.querySelectorAll('#voucher-print-portal img')]
    Promise.race([Promise.all(images.map(whenLoaded)), new Promise((resolve) => setTimeout(resolve, LOAD_TIMEOUT_MS))])
      .then(() => { if (!cancelled) onReady?.(readyKey) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qrs, readyKey])

  if (available.length === 0) return <p className="text-sm text-gray-500">No hay vouchers disponibles para imprimir.</p>

  return (
    <>
      <style>{PRINT_CSS}</style>
      <div className="voucher-screen bg-white"><Pages batch={batch} vouchers={available} qrs={qrs} withBack={withBack} /></div>
      {createPortal(
        <div id="voucher-print-portal" className="bg-white"><Pages batch={batch} vouchers={available} qrs={qrs} withBack={withBack} /></div>,
        document.body,
      )}
    </>
  )
}
