const STATUS = {
  open: ['Abierta', 'bg-amber-100 text-amber-900'],
  billing: ['Cuenta pedida', 'bg-red-100 text-red-800'],
  closed: ['Cerrada', 'bg-green-100 text-green-800'],
  cancelled: ['Anulada', 'bg-gray-200 text-gray-700'],
}

export default function StatusBadge({ status }) {
  const [label, style] = STATUS[status] ?? [status, 'bg-gray-100 text-gray-700']
  return <span className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ${style}`}>{label}</span>
}
