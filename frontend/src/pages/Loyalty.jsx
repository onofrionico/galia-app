import { useState } from 'react'
import { Coffee } from 'lucide-react'
import CustomersTab from '../components/loyalty/CustomersTab'
import HistoryTab from '../components/loyalty/HistoryTab'
import ReportsTab from '../components/loyalty/ReportsTab'
import RewardsTab from '../components/loyalty/RewardsTab'
import SettingsTab from '../components/loyalty/SettingsTab'
import VariantsTab from '../components/loyalty/VariantsTab'

const TABS = [
  ['customers', 'Clientes', CustomersTab],
  ['rewards', 'Premios', RewardsTab],
  ['variants', 'Cafecitos por producto', VariantsTab],
  ['reports', 'Reportes', ReportsTab],
  ['history', 'Historial', HistoryTab],
  ['settings', 'Configuración', SettingsTab],
]

export default function Loyalty() {
  const [tab, setTab] = useState('customers')
  const Current = TABS.find(([id]) => id === tab)[2]
  return (
    <div className="space-y-4 p-4 md:p-6">
      <h1 className="flex items-center gap-2 text-2xl font-bold text-galia-plum"><Coffee /> Fidelización</h1>
      <div className="flex gap-1 overflow-x-auto border-b" role="tablist">
        {TABS.map(([id, label]) => (
          <button key={id} type="button" role="tab" aria-selected={tab === id} onClick={() => setTab(id)}
            className={`whitespace-nowrap px-3 py-2 text-sm font-medium ${tab === id ? 'border-b-2 border-galia-plum text-galia-plum' : 'text-gray-600'}`}>
            {label}
          </button>
        ))}
      </div>
      <div className="rounded-xl bg-white p-4 shadow-sm"><Current /></div>
    </div>
  )
}
