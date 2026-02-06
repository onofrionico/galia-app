import { useState, useEffect } from 'react'
import { jobPositionService } from '../services/jobPositionService'
import { Plus, Edit2, X, Save, Briefcase, DollarSign, Clock, TrendingUp } from 'lucide-react'

const JobPositions = () => {
  const [positions, setPositions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [editingPosition, setEditingPosition] = useState(null)
  const [saving, setSaving] = useState(false)

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    contract_type: 'por_hora',
    base_salary: '',
    hourly_rate: '',
    standard_hours_per_week: '',
    standard_hours_per_month: '',
    overtime_rate_multiplier: '1.5',
    weekend_rate_multiplier: '1.25',
    holiday_rate_multiplier: '2.0'
  })

  useEffect(() => {
    loadPositions()
  }, [])

  const loadPositions = async () => {
    try {
      setLoading(true)
      const data = await jobPositionService.getJobPositions()
      setPositions(data || [])
      setError(null)
    } catch (err) {
      setError('Error al cargar puestos: ' + (err.response?.data?.error || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleOpenModal = (position = null) => {
    if (position) {
      setEditingPosition(position)
      setFormData({
        name: position.name || '',
        description: position.description || '',
        contract_type: position.contract_type || 'por_hora',
        base_salary: position.base_salary || '',
        hourly_rate: position.hourly_rate || '',
        standard_hours_per_week: position.standard_hours_per_week || '',
        standard_hours_per_month: position.standard_hours_per_month || '',
        overtime_rate_multiplier: position.overtime_rate_multiplier || '1.5',
        weekend_rate_multiplier: position.weekend_rate_multiplier || '1.25',
        holiday_rate_multiplier: position.holiday_rate_multiplier || '2.0'
      })
    } else {
      setEditingPosition(null)
      setFormData({
        name: '',
        description: '',
        contract_type: 'por_hora',
        base_salary: '',
        hourly_rate: '',
        standard_hours_per_week: '',
        standard_hours_per_month: '',
        overtime_rate_multiplier: '1.5',
        weekend_rate_multiplier: '1.25',
        holiday_rate_multiplier: '2.0'
      })
    }
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingPosition(null)
    setError(null)
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData({ ...formData, [name]: value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      setSaving(true)
      setError(null)

      const dataToSend = {
        ...formData,
        base_salary: formData.base_salary ? parseFloat(formData.base_salary) : null,
        hourly_rate: formData.hourly_rate ? parseFloat(formData.hourly_rate) : null,
        standard_hours_per_week: formData.standard_hours_per_week ? parseInt(formData.standard_hours_per_week) : null,
        standard_hours_per_month: formData.standard_hours_per_month ? parseInt(formData.standard_hours_per_month) : null,
        overtime_rate_multiplier: parseFloat(formData.overtime_rate_multiplier),
        weekend_rate_multiplier: parseFloat(formData.weekend_rate_multiplier),
        holiday_rate_multiplier: parseFloat(formData.holiday_rate_multiplier)
      }

      if (editingPosition) {
        await jobPositionService.updateJobPosition(editingPosition.id, dataToSend)
      } else {
        await jobPositionService.createJobPosition(dataToSend)
      }

      await loadPositions()
      handleCloseModal()
    } catch (err) {
      setError(err.response?.data?.error || 'Error al guardar puesto')
    } finally {
      setSaving(false)
    }
  }

  const handleToggleActive = async (position) => {
    try {
      if (position.is_active) {
        await jobPositionService.deactivateJobPosition(position.id)
      } else {
        await jobPositionService.activateJobPosition(position.id)
      }
      await loadPositions()
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cambiar estado del puesto')
    }
  }

  const getContractTypeLabel = (type) => {
    const types = {
      por_hora: 'Por Hora',
      part_time: 'Part Time',
      full_time: 'Full Time'
    }
    return types[type] || type
  }

  const getContractTypeBadge = (type) => {
    const typeConfig = {
      por_hora: { bg: 'bg-blue-100', text: 'text-blue-800' },
      part_time: { bg: 'bg-purple-100', text: 'text-purple-800' },
      full_time: { bg: 'bg-green-100', text: 'text-green-800' }
    }
    const config = typeConfig[type] || { bg: 'bg-gray-100', text: 'text-gray-800' }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {getContractTypeLabel(type)}
      </span>
    )
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Puestos de Trabajo</h1>
        <button
          onClick={() => handleOpenModal()}
          className="flex items-center justify-center gap-2 bg-blue-600 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm md:text-base w-full sm:w-auto"
        >
          <Plus size={18} />
          Nuevo Puesto
        </button>
      </div>

      {error && !showModal && (
        <div className="bg-red-50 border-l-4 border-red-500 p-3 md:p-4 text-red-700 text-sm md:text-base">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {loading ? (
          <div className="p-6 md:p-8 text-center text-gray-500 text-sm md:text-base">
            Cargando puestos...
          </div>
        ) : positions.length === 0 ? (
          <div className="p-6 md:p-8 text-center text-gray-500 text-sm md:text-base">
            No hay puestos de trabajo registrados
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {positions.map((position) => (
              <div key={position.id} className="p-4 md:p-6 hover:bg-gray-50 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <Briefcase size={18} className="text-gray-400 flex-shrink-0" />
                      <h3 className="text-base md:text-lg font-semibold text-gray-900 truncate">{position.name}</h3>
                      {getContractTypeBadge(position.contract_type)}
                      {!position.is_active && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded">
                          Inactivo
                        </span>
                      )}
                    </div>
                    
                    {position.description && (
                      <p className="text-xs md:text-sm text-gray-600 mb-3 line-clamp-2">{position.description}</p>
                    )}

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 md:gap-4 mt-3">
                      {position.contract_type === 'por_hora' ? (
                        <div className="flex items-center gap-2 text-xs md:text-sm">
                          <DollarSign size={14} className="text-gray-400 flex-shrink-0" />
                          <span className="text-gray-600">Tarifa:</span>
                          <span className="font-medium text-gray-900">
                            ${position.hourly_rate?.toLocaleString('es-AR')}/h
                          </span>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center gap-2 text-xs md:text-sm">
                            <DollarSign size={14} className="text-gray-400 flex-shrink-0" />
                            <span className="text-gray-600">Salario:</span>
                            <span className="font-medium text-gray-900 truncate">
                              ${position.base_salary?.toLocaleString('es-AR')}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-xs md:text-sm">
                            <Clock size={14} className="text-gray-400 flex-shrink-0" />
                            <span className="text-gray-600">Horas/sem:</span>
                            <span className="font-medium text-gray-900">
                              {position.standard_hours_per_week}
                            </span>
                          </div>
                        </>
                      )}
                      
                      <div className="flex items-center gap-2 text-xs md:text-sm">
                        <TrendingUp size={14} className="text-gray-400 flex-shrink-0" />
                        <span className="text-gray-600">Extras:</span>
                        <span className="font-medium text-gray-900">
                          {position.overtime_rate_multiplier}x
                        </span>
                      </div>
                    </div>

                    {position.employee_count !== undefined && (
                      <div className="mt-3 text-xs md:text-sm text-gray-500">
                        {position.employee_count} empleado{position.employee_count !== 1 ? 's' : ''} asignado{position.employee_count !== 1 ? 's' : ''}
                      </div>
                    )}
                  </div>

                  <div className="flex gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleOpenModal(position)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Editar"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => handleToggleActive(position)}
                      className={`px-2 md:px-3 py-1 text-xs md:text-sm rounded-lg transition-colors whitespace-nowrap ${
                        position.is_active
                          ? 'text-red-600 hover:bg-red-50'
                          : 'text-green-600 hover:bg-green-50'
                      }`}
                    >
                      {position.is_active ? 'Desact.' : 'Activ.'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">
                {editingPosition ? 'Editar Puesto' : 'Nuevo Puesto'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {error && (
                <div className="bg-red-50 border-l-4 border-red-500 p-4 text-red-700">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre del Puesto <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Ej: Barista, Cajero, Encargado"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descripción
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows="3"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Descripción del puesto..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Contrato <span className="text-red-500">*</span>
                </label>
                <select
                  name="contract_type"
                  value={formData.contract_type}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="por_hora">Por Hora</option>
                  <option value="part_time">Part Time</option>
                  <option value="full_time">Full Time</option>
                </select>
              </div>

              {formData.contract_type === 'por_hora' ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tarifa por Hora ($) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    name="hourly_rate"
                    value={formData.hourly_rate}
                    onChange={handleChange}
                    required
                    min="0"
                    step="0.01"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="2500.00"
                  />
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Salario Base Mensual ($) <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="number"
                        name="base_salary"
                        value={formData.base_salary}
                        onChange={handleChange}
                        required
                        min="0"
                        step="0.01"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="450000.00"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Horas Semanales Estándar <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="number"
                        name="standard_hours_per_week"
                        value={formData.standard_hours_per_week}
                        onChange={handleChange}
                        required
                        min="0"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="40"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Horas Mensuales Estándar
                    </label>
                    <input
                      type="number"
                      name="standard_hours_per_month"
                      value={formData.standard_hours_per_month}
                      onChange={handleChange}
                      min="0"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="160"
                    />
                  </div>
                </>
              )}

              <div className="border-t pt-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Multiplicadores de Tarifa</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Horas Extras
                    </label>
                    <input
                      type="number"
                      name="overtime_rate_multiplier"
                      value={formData.overtime_rate_multiplier}
                      onChange={handleChange}
                      min="1"
                      step="0.01"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="1.5"
                    />
                    <p className="text-xs text-gray-500 mt-1">Ej: 1.5 = 50% adicional</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Fin de Semana
                    </label>
                    <input
                      type="number"
                      name="weekend_rate_multiplier"
                      value={formData.weekend_rate_multiplier}
                      onChange={handleChange}
                      min="1"
                      step="0.01"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="1.25"
                    />
                    <p className="text-xs text-gray-500 mt-1">Ej: 1.25 = 25% adicional</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Feriados
                    </label>
                    <input
                      type="number"
                      name="holiday_rate_multiplier"
                      value={formData.holiday_rate_multiplier}
                      onChange={handleChange}
                      min="1"
                      step="0.01"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="2.0"
                    />
                    <p className="text-xs text-gray-500 mt-1">Ej: 2.0 = 100% adicional</p>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
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

export default JobPositions
