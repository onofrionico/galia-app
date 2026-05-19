import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, Save, X, AlertCircle, TestTube2 } from 'lucide-react'
import { GALIA } from '../../constants/colors'
import configurationService from '../../services/configurationService'

const PRINTER_TYPES = [
  { value: 'comanda', label: 'Comanda' },
  { value: 'control', label: 'Control' },
]

export default function PrinterDevicesManager() {
  const [printers, setPrinters] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingPrinter, setEditingPrinter] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    type: 'comanda',
    ip_address: '',
    port: '9100',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(null)
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    fetchPrinters()
  }, [])

  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 3000)
      return () => clearTimeout(timer)
    }
  }, [successMessage])

  const fetchPrinters = async () => {
    setLoading(true)
    try {
      const response = await configurationService.getPrinters()
      setPrinters(Array.isArray(response) ? response : response.devices || response.dispositivos || [])
    } catch (error) {
      console.error('Error fetching printers:', error)
      setError('Error al cargar los dispositivos de impresión')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenModal = (printer = null) => {
    if (printer) {
      setEditingPrinter(printer)
      setFormData({
        name: printer.name || '',
        type: printer.type || 'comanda',
        ip_address: printer.ip_address || '',
        port: printer.port?.toString() || '9100',
      })
    } else {
      setEditingPrinter(null)
      setFormData({
        name: '',
        type: 'comanda',
        ip_address: '',
        port: '9100',
      })
    }
    setError('')
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingPrinter(null)
    setFormData({
      name: '',
      type: 'comanda',
      ip_address: '',
      port: '9100',
    })
    setError('')
  }

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError('El nombre del dispositivo es requerido')
      return false
    }
    if (!formData.ip_address.trim()) {
      setError('La dirección IP es requerida')
      return false
    }
    if (!formData.port.toString().trim()) {
      setError('El puerto es requerido')
      return false
    }
    if (isNaN(formData.port)) {
      setError('El puerto debe ser un número')
      return false
    }
    // Basic IP validation
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/
    if (!ipRegex.test(formData.ip_address)) {
      setError('Formato de IP inválido')
      return false
    }
    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validateForm()) return

    setError('')
    setSaving(true)

    try {
      const submitData = {
        name: formData.name,
        type: formData.type,
        ip_address: formData.ip_address,
        port: parseInt(formData.port),
      }

      if (editingPrinter) {
        await configurationService.updatePrinter(editingPrinter.id, submitData)
        setSuccessMessage('Dispositivo actualizado correctamente')
      } else {
        await configurationService.createPrinter(submitData)
        setSuccessMessage('Dispositivo creado correctamente')
      }

      handleCloseModal()
      fetchPrinters()
    } catch (error) {
      console.error('Error saving printer:', error)
      setError(error.response?.data?.error || 'Error al guardar el dispositivo')
    } finally {
      setSaving(false)
    }
  }

  const handleTestPrinter = async (printerId) => {
    setTesting(printerId)
    try {
      await configurationService.testPrinter(printerId)
      setSuccessMessage('Prueba de impresora exitosa')
    } catch (error) {
      console.error('Error testing printer:', error)
      setError(error.response?.data?.error || 'Error al probar el dispositivo')
    } finally {
      setTesting(null)
    }
  }

  const handleDelete = async (printer) => {
    if (!confirm(`¿Estás seguro de eliminar el dispositivo "${printer.name}"?`)) {
      return
    }

    try {
      await configurationService.deletePrinter(printer.id)
      setSuccessMessage('Dispositivo eliminado correctamente')
      fetchPrinters()
    } catch (error) {
      console.error('Error deleting printer:', error)
      setError(error.response?.data?.error || 'Error al eliminar el dispositivo')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12" style={{ borderColor: GALIA.marron, borderTopColor: GALIA.amarillo }}></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold" style={{ color: GALIA.marron }}>
          Dispositivos de Impresión
        </h2>
        <button
          onClick={() => handleOpenModal()}
          className="flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-white transition-opacity hover:opacity-90"
          style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
        >
          <Plus size={20} />
          Nuevo Dispositivo
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div className="p-4 rounded-lg flex items-start gap-3" style={{ backgroundColor: '#fef2f2', borderLeft: `4px solid #ef4444` }}>
          <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
          <p style={{ color: '#dc2626' }}>{error}</p>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-lg flex items-start gap-3" style={{ backgroundColor: '#f0fdf4', borderLeft: `4px solid #22c55e` }}>
          <p style={{ color: '#16a34a' }}>{successMessage}</p>
        </div>
      )}

      {/* Printers Table */}
      {printers.length === 0 ? (
        <div className="text-center py-12" style={{ color: GALIA.grisClaro }}>
          <p className="text-lg">No hay dispositivos de impresión registrados</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr style={{ backgroundColor: GALIA.marron }}>
                <th className="px-6 py-3 text-left text-white font-semibold">Nombre</th>
                <th className="px-6 py-3 text-left text-white font-semibold">Tipo</th>
                <th className="px-6 py-3 text-left text-white font-semibold">IP</th>
                <th className="px-6 py-3 text-left text-white font-semibold">Puerto</th>
                <th className="px-6 py-3 text-left text-white font-semibold">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {printers.map((printer) => (
                <tr key={printer.id} style={{ borderBottom: `1px solid ${GALIA.grisLigero}` }}>
                  <td className="px-6 py-4" style={{ color: GALIA.marron, fontWeight: '600' }}>
                    {printer.name}
                  </td>
                  <td className="px-6 py-4" style={{ color: GALIA.grisClaro }}>
                    <span
                      className="px-3 py-1 rounded-full text-sm font-semibold"
                      style={{
                        backgroundColor: GALIA.amarillo,
                        color: GALIA.marron,
                      }}
                    >
                      {PRINTER_TYPES.find(t => t.value === printer.type)?.label || printer.type}
                    </span>
                  </td>
                  <td className="px-6 py-4" style={{ color: GALIA.grisClaro }}>
                    {printer.ip_address}
                  </td>
                  <td className="px-6 py-4" style={{ color: GALIA.grisClaro }}>
                    {printer.port}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleTestPrinter(printer.id)}
                        disabled={testing === printer.id}
                        className="px-3 py-2 rounded font-semibold transition-colors disabled:opacity-50"
                        style={{
                          backgroundColor: GALIA.verde,
                          color: 'white',
                          fontSize: '0.9rem',
                        }}
                        title="Probar dispositivo"
                      >
                        <TestTube2 size={16} />
                      </button>
                      <button
                        onClick={() => handleOpenModal(printer)}
                        className="px-3 py-2 rounded font-semibold transition-colors"
                        style={{
                          backgroundColor: GALIA.amarillo,
                          color: GALIA.marron,
                          fontSize: '0.9rem',
                        }}
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(printer)}
                        className="px-3 py-2 rounded font-semibold text-white transition-colors"
                        style={{ backgroundColor: '#ef4444', fontSize: '0.9rem' }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            {/* Modal Header */}
            <div className="p-6 border-b" style={{ borderColor: GALIA.grisLigero, backgroundColor: GALIA.marron }}>
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-white">
                  {editingPrinter ? 'Editar Dispositivo' : 'Nuevo Dispositivo'}
                </h3>
                <button
                  onClick={handleCloseModal}
                  className="text-white hover:opacity-80"
                >
                  <X size={24} />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {error && (
                <div className="p-3 rounded-lg flex items-start gap-2" style={{ backgroundColor: '#fef2f2' }}>
                  <AlertCircle size={18} className="text-red-600 flex-shrink-0 mt-0.5" />
                  <p style={{ color: '#dc2626', fontSize: '0.9rem' }}>{error}</p>
                </div>
              )}

              <div>
                <label className="block text-sm font-semibold mb-1" style={{ color: GALIA.marron }}>
                  Nombre del Dispositivo *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ej: Impresora Comanda 1"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2"
                  style={{
                    borderColor: GALIA.grisLigero,
                    backgroundColor: GALIA.crema,
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-1" style={{ color: GALIA.marron }}>
                  Tipo de Impresora *
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2"
                  style={{
                    borderColor: GALIA.grisLigero,
                    backgroundColor: GALIA.crema,
                  }}
                >
                  {PRINTER_TYPES.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-1" style={{ color: GALIA.marron }}>
                  Dirección IP *
                </label>
                <input
                  type="text"
                  value={formData.ip_address}
                  onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                  placeholder="Ej: 192.168.1.100"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2"
                  style={{
                    borderColor: GALIA.grisLigero,
                    backgroundColor: GALIA.crema,
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-1" style={{ color: GALIA.marron }}>
                  Puerto *
                </label>
                <input
                  type="number"
                  value={formData.port}
                  onChange={(e) => setFormData({ ...formData, port: e.target.value })}
                  placeholder="Ej: 9100"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2"
                  style={{
                    borderColor: GALIA.grisLigero,
                    backgroundColor: GALIA.crema,
                  }}
                />
              </div>

              {/* Modal Buttons */}
              <div className="flex gap-3 pt-4 border-t" style={{ borderColor: GALIA.grisLigero }}>
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-colors flex-1"
                  style={{
                    backgroundColor: GALIA.grisLigero,
                    color: GALIA.marron,
                  }}
                >
                  <X size={18} />
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50 flex-1"
                  style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
                >
                  <Save size={18} />
                  {saving ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
