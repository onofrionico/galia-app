import { formatMoney } from '../utils/money'

function Row({ label, value, sign = '' }) {
  return (
    <div className="flex justify-between text-sm">
      <dt className="text-gray-600">{label}</dt>
      <dd>{sign}{formatMoney(value)}</dd>
    </div>
  )
}

export default function CashSummaryCards({ summary }) {
  const { cash, methods } = summary
  const others = methods.filter((m) => m.payment_method_id !== cash.payment_method_id)
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <section className="rounded-xl border-2 border-galia-plum/30 bg-white p-4">
        <h3 className="font-semibold text-galia-plum">Efectivo</h3>
        <dl className="mt-2 space-y-1">
          <Row label="Fondo inicial" value={cash.opening_float} />
          <Row label="Ventas" value={cash.sales} sign="+ " />
          {cash.cancelled > 0 && <Row label="Anulaciones" value={cash.cancelled} sign="− " />}
          {cash.expenses > 0 && <Row label="Gastos" value={cash.expenses} sign="− " />}
          {cash.withdrawals > 0 && <Row label="Retiros" value={cash.withdrawals} sign="− " />}
          {cash.deposits > 0 && <Row label="Ingresos" value={cash.deposits} sign="+ " />}
          <div className="flex justify-between border-t pt-2 text-lg font-bold text-galia-plum">
            <dt>Esperado</dt><dd>{formatMoney(cash.expected)}</dd>
          </div>
        </dl>
      </section>
      {others.map((m) => (
        <section key={m.payment_method_id} className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="font-semibold">{m.method_name}</h3>
          <p className="mt-2 text-2xl font-bold">{formatMoney(m.expected)}</p>
          {m.cancelled > 0 && <p className="text-xs text-gray-500">Cobrado {formatMoney(m.collected)} · anulado {formatMoney(m.cancelled)}</p>}
        </section>
      ))}
    </div>
  )
}
