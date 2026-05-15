import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, Save, X, AlertCircle } from 'lucide-react'
import { GALIA } from '../../constants/colors'
import configurationService from '../../services/configurationService'

export default function MesasManager() {
  const [salones, setSalones] = useState([])
  const [selectedSalonId, setSelectedSalonId] = useState(null)
  const [mesas, setMesas] = useState([])
  const [loading, setLoading] = useState(true)
  const [mesasLoading, setMesasLoading] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [editingMesa, setEditingMesa] = useState(null)
  const [formData, setFormData] = useState({
    number: '',
    capacity: '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    fetchSalones()
  }, [])

  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 3000)
      return () => clearTimeout(timer)
    }
  }, [successMessage])

  useEffect(() => {
    if (selectedSalonId) {
      fetchMesas(selectedSalonId)
    }
  }, [selectedSalonId])

  const fetchSalones = async () => {
    setLoading(true)
    try {
      const response = await configurationService.getSalons()
      const salonesList = Array.isArray(response) ? response : response.data || []
      setSalones(salonesList)
      if (salonesList.length > 0) {
        setSelectedSalonId(salonesList[0].id)
      }
    } catch (error) {
      console.error('Error fetching salones:', error)
      setError('Error al cargar los salones')
    } finally {
      setLoading(false)
    }
  }

  const fetchMesas = async (salonId) => {
    setMesasLoading(true)
    try {
      const response = await configurationService.getMesas(salonId)
      setMesas(Array.isArray(response) ? response : response.data || [])
    } catch (error) {
      console.error('Error fetching mesas:', error)
      setError('Error al cargar las mesas')
    } finally {
      setMesasLoading(false)
    }
  }

  const handleOpenModal = (mesa = null) => {
    if (mesa) {
      setEditingMesa(mesa)
      setFormData({
        number: mesa.number || '',
        capacity: mesa.capacity || '',
      })
    } else {
      setEditingMesa(null)
      setFormData({
        number: '',
        capacity: '',
      })
    }
    setError('')
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingMesa(null)
    setFormData({
      number: '',
      capacity: '',
    })
    setError('')
  }

  const validateForm = () => {
    if (!formData.number.toString().trim()) {
      setError('El número de la mesa es requerido')
      return false
    }
    if (!formData.capacity.toString().trim()) {
      setError('La capacidad es requerida')
      return false
    }
    if (isNaN(formData.number) || isNaN(formData.capacity)) {
      setError('El número y capacidad deben ser números')
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
        number: parseInt(formData.number),
        capacity: parseInt(formData.capacity),
      }

      if (editingMesa) {
        await configurationService.updateMesa(selectedSalonId, editingMesa.id, submitData)
        setSuccessMessage('Mesa actualizada correctamente')
      } else {
        await configurationService.createMesa(selectedSalonId, submitData)
        setSuccessMessage('Mesa creada correctamente')
      }

      handleCloseModal()
      fetchMesas(selectedSalonId)
    } catch (error) {
      console.error('Error saving mesa:', error)
      setError(error.response?.data?.error || 'Error al guardar la mesa')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (mesa) => {
    if (!confirm(`¿Estás seguro de eliminar la mesa ${mesa.number}?`)) {
      return
    }

    try {
      await configurationService.deleteMesa(selectedSalonId, mesa.id)
      setSuccessMessage('Mesa eliminada correctamente')
      fetchMesas(selectedSalonId)
    } catch (error) {
      console.error('Error deleting mesa:', error)
      setError(error.response?.data?.error || 'Error al eliminar la mesa')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12" style={{ borderColor: GALIA.marron, borderTopColor: GALIA.amarillo }}></div>
      </div>
    )
  }

  if (salones.length === 0) {
    return (
      <div className="text-center py-12" style={{ color: GALIA.grisClaro }}>
        <p className="text-lg">No hay salones registrados. Crea un salón primero.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold" style={{ color: GALIA.marron }}>
          Mesas
        </h2>
        <button
          onClick={() => handleOpenModal()}
          className="flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-white transition-opacity hover:opacity-90"
          style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
        >
          <Plus size={20} />
          Nueva Mesa
        </button>
      </div>

      {/* Salon Selector */}
      <div>
        <label className="block text-sm font-semibold mb-2" style={{ color: GALIA.marron }}>
          Seleccionar Salón
        </label>
        <select
          value={selectedSalonId || ''}
          onChange={(e) => setSelectedSalonId(parseInt(e.target.value))}
          className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2"
          style={{
            borderColor: GALIA.grisLigero,
            backgroundColor: GALIA.crema,
          }}
        >
          <option value="">-- Seleccionar --</option>
          {salones.map((salon) => (
            <option key={salon.id} value={salon.id}>
              {salon.name}
            </option>
          ))}
        </select>
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

      {/* Mesas Table */}
      {mesasLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12" style={{ borderColor: GALIA.marron, borderTopColor: GALIA.amarillo }}></div>
        </div>
      ) : mesas.length === 0 ? (
        <div className="text-center py-12" style={{ color: GALIA.grisClaro }}>
          <p className="text-lg">No hay mesas registradas en este salón</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr style={{ backgroundColor: GALIA.marron }}>
                <th className="px-6 py-3 text-left text-white font-semibold">Mesa</th>
                <th className="px-6 py-3 text-left text-white font-semibold">Capacidad</th>
                <th className="px-6 py-3 text-left text-white font-semibold">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {mesas.map((mesa) => (
                <tr key={mesa.id} style={{ borderBottom: `1px solid ${GALIA.grisLigero}` }}>
                  <td className="px-6 py-4" style={{ color: GALIA.marron, fontWeight: '600' }}>
                    Mesa {mesa.number}
                  </td>
                  <td className="px-6 py-4" style={{ color: GALIA.grisClaro }}>
                    {mesa.capacity} personas
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleOpenModal(mesa)}
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
                        onClick={() => handleDelete(mesa)}
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
                  {editingMesa ? 'Editar Mesa' : 'Nueva Mesa'}
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
                  Número de Mesa *
                </label>
                <input
                  type="number"
                  value={formData.number}
                  onChange={(e) => setFormData({ ...formData, number: e.target.value })}
                  placeholder="Ej: 1"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2"
                  style={{
                    borderColor: GALIA.grisLigero,
                    backgroundColor: GALIA.crema,
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-1" style={{ color: GALIA.marron }}>
                  Capacidad (personas) *
                </label>
                <input
                  type="number"
                  value={formData.capacity}
                  onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                  placeholder="Ej: 4"
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
