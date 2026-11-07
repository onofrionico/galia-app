// Qué premios le alcanzan al cliente y cuánto le falta para los demás.
export function reachable(balance, rewards) {
  const available = rewards.filter((r) => r.cost <= balance)
  const next = rewards.filter((r) => r.cost > balance).map((reward) => ({ reward, missing: reward.cost - balance }))
  return { available, next }
}
