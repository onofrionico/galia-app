import { useEffect, useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import api from '@/services/api'
import { posCashApi } from '../api/posApi'
import { useCashMutation, useExpenseCategories } from '../hooks/useCash'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { parseAmount } from '../utils/money'

const TITLES = { expense: 'Gasto de caja', withdrawal: 'Retiro de efectivo', deposit: 'Ingreso de efectivo' }
const field = 'mt-1 w-full rounded-lg border border-gray-300 px-3 py-2'

// kind: 'expense' | 'withdrawal' | 'deposit'.
export default function MovementModal({ session, kind, onClose }) {
  const { hasModuleAccess } = useAuth()
  const isExpense = kind === 'expense'
  const canPickSupplier = isExpense && hasModuleAccess('Suppliers')
  const { data: categories = [] } = useExpenseCategories(isExpense)
  const [suppliers, setSuppliers] = useState([])
  const [amount, setAmount] = useState('')
  const [reason, setReason] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [supplierId, setSupplierId] = useState('')
  const [error, setError] = useState('')
  const { run, busy } = useCashMutation()

  useEffect(() => {
    if (!canPickSupplier) return
    api.get('/suppliers').then((r) => setSuppliers((r.data.suppliers ?? []).filter((s) => s.is_active)))
      .catch(() => setSuppliers([]))
  }, [canPickSupplier])

  const submit = async () => {
    const value = parseAmount(amount)
    if (!(value > 0)) return setError('Indicá el monto')
    if (!reason.trim()) return setError('Indicá el motivo')
    if (isExpense && !categoryId) return setError('Elegí la categoría del gasto')
    const body = { kind, amount: value, reason: reason.trim() }
    if (isExpense) {
      body.category_id = Number(categoryId)
      if (supplierId) body.supplier_id = Number(supplierId)
    }
    if (await run(() => posCashApi.addMovement(session.id, body))) onClose()
  }

  const footer = (
    <div className="flex justify-end gap-2">
      <button type="button" className={btn('secondary')} onClick={onClose}>Cancelar</button>
      <button type="button" className={btn('primary')} disabled={busy} onClick={submit}>Registrar</button>
    </div>
  )

  return (
    <Modal title={TITLES[kind]} onClose={onClose} size="sm" footer={footer}>
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">Monto
          <input inputMode="decimal" autoFocus value={amount} onChange={(e) => { setAmount(e.target.value); setError('') }}
            className={`${field} text-xl`} />
        </label>
        <label className="block text-sm font-medium text-gray-700">Motivo
          <input value={reason} maxLength={255} onChange={(e) => { setReason(e.target.value); setError('') }} className={field} />
        </label>
        {isExpense && (
          <label className="block text-sm font-medium text-gray-700">Categoría
            <select value={categoryId} onChange={(e) => { setCategoryId(e.target.value); setError('') }} className={field}>
              <option value="">Elegí una categoría</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </label>
        )}
        {canPickSupplier && (
          <label className="block text-sm font-medium text-gray-700">Proveedor (opcional)
            <select value={supplierId} onChange={(e) => setSupplierId(e.target.value)} className={field}>
              <option value="">Sin proveedor</option>
              {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </label>
        )}
        {error && <p className="text-sm text-red-700">{error}</p>}
      </div>
    </Modal>
  )
}
