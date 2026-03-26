import React, { useState } from 'react'
import { Settings, List, DollarSign } from 'lucide-react'
import ConfigurableListManager from '../components/configuration/ConfigurableListManager'
import ExchangeRateManager from '../components/configuration/ExchangeRateManager'

export default function ConfigurationPage() {
  const [activeTab, setActiveTab] = useState('lists')

  const configurableLists = [
    {
      type: 'product_category',
      title: 'Categorías de Productos',
      description: 'Categorías para clasificar productos en el catálogo'
    },
    {
      type: 'unit_of_measure',
      title: 'Unidades de Medida',
      description: 'Unidades para medir cantidades de productos (kg, L, unidad, etc.)'
    },
    {
      type: 'payment_term',
      title: 'Términos de Pago',
      description: 'Condiciones de pago para proveedores (contado, 30 días, etc.)'
    },
    {
      type: 'supplier_type',
      title: 'Tipos de Proveedor',
      description: 'Clasificación de proveedores por tipo de servicio'
    }
  ]

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Settings className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Configuración</h1>
        </div>
        <p className="text-gray-600">
          Gestiona listas configurables y tipos de cambio para el sistema
        </p>
      </div>

      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('lists')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'lists'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <List className="w-5 h-5" />
              <span>Listas Configurables</span>
            </button>
            <button
              onClick={() => setActiveTab('exchange')}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'exchange'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <DollarSign className="w-5 h-5" />
              <span>Tipos de Cambio</span>
            </button>
          </nav>
        </div>
      </div>

      {activeTab === 'lists' && (
        <div className="space-y-6">
          {configurableLists.map((list) => (
            <ConfigurableListManager
              key={list.type}
              listType={list.type}
              title={list.title}
              description={list.description}
            />
          ))}
        </div>
      )}

      {activeTab === 'exchange' && (
        <ExchangeRateManager />
      )}
    </div>
  )
}
