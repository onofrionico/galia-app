import { TABLE_STATUS_STYLES } from '@/pos/floor/tableStyles'
import { tableStatus, tableSummary } from '@/pos/utils/floor'
import { formatMoney } from '@/pos/utils/money'
import { elapsedLabel } from '@/pos/utils/time'
import { hasPending, waiterLabel } from './utils/tableFilters'

export default function TableCard({ table, userId, now, onClick }) {
  const status = tableStatus(table)
  const summary = tableSummary(table)
  const pending = hasPending(table)

  return (
    <button type="button" onClick={onClick}
      aria-label={`${table.label}${status === 'free' ? ', libre' : `, ${formatMoney(summary.total)}`}${pending ? ', con ítems sin confirmar' : ''}`}
      className={`relative flex min-h-[104px] flex-col justify-between rounded-xl border-2 p-3 text-left ${TABLE_STATUS_STYLES[status]}`}>
      <span className="flex w-full items-start justify-between gap-2">
        <span className="text-lg font-semibold leading-tight">{table.label}</span>
        {summary.count > 1 && (
          <span className="whitespace-nowrap rounded-full bg-galia-plum px-2 py-0.5 text-xs text-galia-cream">{summary.count} cuentas</span>
        )}
      </span>
      {status === 'free' ? (
        <span className="text-sm">Libre</span>
      ) : (
        <span className="text-sm leading-tight">
          <span className="block text-base font-semibold">{formatMoney(summary.total)}</span>
          <span className="block truncate">{waiterLabel(table, userId)}</span>
          <span className="block">{elapsedLabel(summary.openedAt, now)}</span>
        </span>
      )}
      {pending && <span className="absolute bottom-3 right-3 h-3 w-3 rounded-full bg-galia-plum" aria-hidden="true" />}
    </button>
  )
}
