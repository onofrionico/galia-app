export function customerChip(customer, preview = 0) {
  const base = `${customer.full_name} · ${customer.balance ?? 0} ☕`
  return preview > 0 ? `${base} · +${preview}` : base
}

export function missingFor(balance, cost) {
  return Math.max(0, cost - (balance ?? 0))
}
