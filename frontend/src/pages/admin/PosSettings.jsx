import { useState } from 'react'
import CatalogEditor from '@/components/pos-settings/CatalogEditor'

const TABS = {
  'payment-methods': {
    label: 'Medios de pago',
    emptyItem: { name: '', kind: 'cash', position: 0, is_active: true },
    fields: [
      { key: 'name', label: 'Nombre', type: 'text' },
      { key: 'kind', label: 'Tipo', type: 'select', options: [['cash', 'Efectivo'], ['card', 'Tarjeta'], ['transfer', 'Transferencia'], ['other', 'Otro']] },
      { key: 'position', label: 'Orden', type: 'number' },
      { key: 'is_active', label: 'Activo', type: 'checkbox' },
    ],
  },
  'discount-templates': {
    label: 'Plantillas de descuento',
    emptyItem: { name: '', kind: 'percent', value: '', scope: 'sale', restricted: false, is_active: true },
    fields: [
      { key: 'name', label: 'Nombre', type: 'text' },
      { key: 'kind', label: 'Tipo', type: 'select', options: [['percent', 'Porcentaje'], ['amount', 'Monto']] },
      { key: 'value', label: 'Valor', type: 'number' },
      { key: 'scope', label: 'Aplica a', type: 'select', options: [['sale', 'La venta'], ['item', 'Un ítem']] },
      { key: 'restricted', label: 'Requiere permiso Descuentos', type: 'checkbox' },
      { key: 'is_active', label: 'Activa', type: 'checkbox' },
    ],
  },
  'cancel-reasons': {
    label: 'Motivos de anulación',
    emptyItem: { name: '', position: 0, is_active: true },
    fields: [
      { key: 'name', label: 'Motivo', type: 'text' },
      { key: 'position', label: 'Orden', type: 'number' },
      { key: 'is_active', label: 'Activo', type: 'checkbox' },
    ],
  },
}

export default function PosSettings() {
  const [tab, setTab] = useState('payment-methods')
  const current = TABS[tab]
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Ajustes del POS</h1>
      <div className="flex gap-1 border-b">
        {Object.entries(TABS).map(([key, { label }]) => (
          <button key={key} type="button" onClick={() => setTab(key)}
            className={`px-4 py-2 font-medium ${tab === key ? 'border-b-2 border-galia-plum text-galia-plum' : 'text-gray-600'}`}>
            {label}
          </button>
        ))}
      </div>
      <CatalogEditor key={tab} resource={tab} fields={current.fields} emptyItem={current.emptyItem} />
    </div>
  )
}
