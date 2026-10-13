import { useMainRegister } from '../hooks/useCash'
import { cashStatusLabel } from '../utils/cashMath'

export default function CashStatusBadge() {
  const { register, isLoading, isError } = useMainRegister()
  if (isLoading || isError) return null
  const open = Boolean(register?.open_session)
  return (
    <span className={`hidden whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium md:inline-block ${
      open ? 'bg-green-100 text-green-800' : 'bg-white/15 text-galia-cream'}`}>
      {cashStatusLabel(register)}
    </span>
  )
}
