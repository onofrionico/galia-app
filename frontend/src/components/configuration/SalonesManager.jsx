import { useState, useEffect } from 'react'
import { Plus, Edit2, Trash2, Save, X, AlertCircle } from 'lucide-react'
import { GALIA } from '../../constants/colors'
import configurationService from '../../services/configurationService'

export default function SalonesManager() {
  const [salones, setSalones] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingSalon, setEditingSalon] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
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

  const fetchSalones = async () => {
    setLoading(true)
    try {
      const response = await configurationService.getSalons()
      setSalones(Array.isArray(response) ? response : response.salones || response.salons || [])
    } catch (error) {
      console.error('Error fetching salones:', error)
      setError('Error al cargar los salones')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenModal = (salon = null) => {
    if (salon) {
      setEditingSalon(salon)
      setFormData({
        name: salon.name || '',
        description: salon.description || '',
      })
    } else {
      setEditingSalon(null)
      setFormData({
        name: '',
        description: '',
      })
    }
    setError('')
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingSalon(null)
    setFormData({
      name: '',
      description: '',
    })
    setError('')
  }

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError('El nombre del salón es requerido')
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
      if (editingSalon) {
        await configurationService.updateSalon(editingSalon.id, formData)
        setSuccessMessage('Salón actualizado correctamente')
      } else {
        await configurationService.createSalon(formData)
        setSuccessMessage('Salón creado correctamente')
      }

      handleCloseModal()
      fetchSalones()
    } catch (error) {
      console.error('Error saving salon:', error)
      setError(error.response?.data?.error || 'Error al guardar el salón')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (salon) => {
    if (!confirm(`¿Estás seguro de eliminar el salón "${salon.name}"?`)) {
      return
    }

    try {
      await configurationService.deleteSalon(salon.id)
      setSuccessMessage('Salón eliminado correctamente')
      fetchSalones()
    } catch (error) {
      console.error('Error deleting salon:', error)
      setError(error.response?.data?.error || 'Error al eliminar el salón')
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
          Salones
        </h2>
        <button
          onClick={() => handleOpenModal()}
          className="flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-white transition-opacity hover:opacity-90"
          style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
        >
          <Plus size={20} />
          Nuevo Salón
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

      {/* Salones Grid */}
      {salones.length === 0 ? (
        <div className="text-center py-12" style={{ color: GALIA.grisClaro }}>
          <p className="text-lg">No hay salones registrados</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {salones.map((salon) => (
            <div
              key={salon.id}
              className="rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
              style={{ backgroundColor: GALIA.blanco, borderTop: `4px solid ${GALIA.marron}` }}
            >
              <h3 className="font-bold text-lg mb-2" style={{ color: GALIA.marron }}>
                {salon.name}
              </h3>
              {salon.description && (
                <p className="mb-4" style={{ color: GALIA.grisClaro, fontSize: '0.95rem' }}>
                  {salon.description}
                </p>
              )}
              <div className="flex gap-2 pt-4 border-t" style={{ borderColor: GALIA.grisLigero }}>
                <button
                  onClick={() => handleOpenModal(salon)}
                  className="flex items-center gap-2 px-3 py-2 rounded font-semibold transition-colors flex-1"
                  style={{
                    backgroundColor: GALIA.amarillo,
                    color: GALIA.marron,
                    fontSize: '0.9rem',
                  }}
                >
                  <Edit2 size={16} />
                  Editar
                </button>
                <button
                  onClick={() => handleDelete(salon)}
                  className="flex items-center gap-2 px-3 py-2 rounded font-semibold text-white transition-colors flex-1"
                  style={{ backgroundColor: '#ef4444', fontSize: '0.9rem' }}
                >
                  <Trash2 size={16} />
                  Eliminar
                </button>
              </div>
            </div>
          ))}
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
                  {editingSalon ? 'Editar Salón' : 'Nuevo Salón'}
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
                  Nombre *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ej: Salón Principal"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2"
                  style={{
                    borderColor: GALIA.grisLigero,
                    backgroundColor: GALIA.crema,
                  }}
                  onFocus={(e) => (e.target.style.ring = GALIA.marron)}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-1" style={{ color: GALIA.marron }}>
                  Descripción
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Descripción del salón (opcional)"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 resize-none"
                  rows="3"
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
