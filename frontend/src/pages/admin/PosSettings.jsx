import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import CatalogEditor from '@/components/pos-settings/CatalogEditor'
import { posConfigApi } from '@/pos/api/posApi'

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
  'print-stations': {
    label: 'Estaciones',
    emptyItem: { name: '', position: 0, is_active: true },
    fields: [
      { key: 'name', label: 'Nombre', type: 'text' },
      { key: 'position', label: 'Orden', type: 'number' },
      { key: 'is_active', label: 'Activa', type: 'checkbox' },
    ],
  },
  printers: {
    label: 'Impresoras',
    emptyItem: {
      name: '', connection: 'network', host: '', port: 9100, os_name: '', paper_width: 80, print_point: 'Caja',
      station_id: '', is_cashier: false, is_active: true,
    },
    fields: [
      { key: 'name', label: 'Nombre', type: 'text' },
      { key: 'connection', label: 'Conexión', type: 'select', options: [['network', 'Red (IP)'], ['usb', 'USB (Windows)']] },
      { key: 'host', label: 'IP (red)', type: 'text' },
      { key: 'port', label: 'Puerto (red)', type: 'number' },
      { key: 'os_name', label: 'Nombre en Windows (USB)', type: 'text' },
      { key: 'paper_width', label: 'Papel', type: 'select', numeric: true, options: [[80, '80 mm'], [58, '58 mm']] },
      { key: 'print_point', label: 'Punto de impresión', type: 'text' },
      { key: 'station_id', label: 'Estación', type: 'select', numeric: true, options: [] },
      { key: 'is_cashier', label: 'Impresora de caja', type: 'checkbox' },
      { key: 'is_active', label: 'Activa', type: 'checkbox' },
    ],
  },
}

export default function PosSettings() {
  const [tab, setTab] = useState('payment-methods')
  // Las opciones de "Estación" de las impresoras salen de las estaciones activas.
  const { data: stations = [] } = useQuery({
    queryKey: ['pos-settings', 'print-stations'],
    queryFn: () => posConfigApi.listResource('print-stations'),
    enabled: tab === 'printers',
  })
  const stationOptions = [['', 'Sin estación'], ...stations.filter((s) => s.is_active).map((s) => [s.id, s.name])]
  const current = tab === 'printers'
    ? { ...TABS.printers, fields: TABS.printers.fields.map((f) => (f.key === 'station_id' ? { ...f, options: stationOptions } : f)) }
    : TABS[tab]
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Ajustes del POS</h1>
      <div className="flex gap-1 overflow-x-auto border-b">
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
