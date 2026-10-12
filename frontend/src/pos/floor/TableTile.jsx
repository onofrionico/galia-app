import { formatMoney } from '../utils/money'
import { tableStatus, tableSummary } from '../utils/floor'
import { elapsedLabel } from '../utils/time'

const STATUS_STYLES = {
  free: 'border-gray-300 bg-white text-gray-700',
  open: 'border-amber-400 bg-amber-100 text-amber-900',
  billing: 'border-red-400 bg-red-100 text-red-900',
}

export default function TableTile({ table, scale, selected, picking, now, onClick }) {
  const status = tableStatus(table)
  const summary = tableSummary(table)
  const disabled = picking && status !== 'free'
  const ring = selected ? 'ring-4 ring-galia-plum/60' : picking && status === 'free' ? 'ring-4 ring-galia-lime' : ''

  return (
    <button type="button" onClick={onClick} disabled={disabled}
      aria-label={`${table.label}${status === 'free' ? ', libre' : `, ${formatMoney(summary.total)}`}`}
      className={`absolute flex flex-col justify-between overflow-hidden rounded-lg border-2 p-1.5 text-left text-xs transition ${STATUS_STYLES[status]} ${ring} ${disabled ? 'opacity-40' : ''}`}
      style={{ left: table.pos_x * scale, top: table.pos_y * scale, width: table.width * scale, height: table.height * scale }}>
      <span className="flex w-full items-center justify-between gap-1 text-sm font-semibold">
        <span className="truncate">{table.label}</span>
        {summary.count > 1 && (
          <span className="whitespace-nowrap rounded-full bg-galia-plum px-1.5 text-[10px] text-galia-cream">{summary.count} cuentas</span>
        )}
      </span>
      {status !== 'free' && (
        <span className="w-full leading-tight">
          <span className="block font-semibold">{formatMoney(summary.total)}</span>
          <span className="block truncate">{summary.waiter}</span>
          <span className="block">{elapsedLabel(summary.openedAt, now)}</span>
        </span>
      )}
    </button>
  )
}
