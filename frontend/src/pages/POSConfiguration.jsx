import { useState } from 'react'
import { GALIA } from '../constants/colors'
import SalonesManager from '../components/configuration/SalonesManager'
import MesasManager from '../components/configuration/MesasManager'
import PrinterDevicesManager from '../components/configuration/PrinterDevicesManager'

const TABS = [
  { id: 'salones', label: 'Salones' },
  { id: 'mesas', label: 'Mesas' },
  { id: 'printers', label: 'Dispositivos de Impresión' },
]

export default function POSConfiguration() {
  const [activeTab, setActiveTab] = useState('salones')

  const renderContent = () => {
    switch (activeTab) {
      case 'salones':
        return <SalonesManager />
      case 'mesas':
        return <MesasManager />
      case 'printers':
        return <PrinterDevicesManager />
      default:
        return <SalonesManager />
    }
  }

  return (
    <div className="min-h-screen p-6" style={{ backgroundColor: GALIA.crema }}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2" style={{ color: GALIA.marron }}>
            Configuración POS
          </h1>
          <p style={{ color: GALIA.grisClaro }}>
            Gestiona los salones, mesas y dispositivos de impresión
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8 border-b" style={{ borderColor: GALIA.grisLigero }}>
          <div className="flex gap-0">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="px-6 py-4 font-semibold transition-colors relative"
                style={{
                  color: activeTab === tab.id ? GALIA.marron : GALIA.grisClaro,
                  fontSize: '1rem',
                }}
              >
                {tab.label}
                {activeTab === tab.id && (
                  <div
                    className="absolute bottom-0 left-0 right-0 h-1"
                    style={{ backgroundColor: GALIA.amarillo }}
                  />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg p-8 shadow-sm">
          {renderContent()}
        </div>
      </div>
    </div>
  )
}
