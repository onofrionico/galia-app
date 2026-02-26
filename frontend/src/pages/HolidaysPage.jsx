import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'
import { Calendar, Plus, Trash2, Edit2, Save, X } from 'lucide-react'
import api from '@/services/api'

const HolidaysPage = () => {
  const [isCreating, setIsCreating] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [formData, setFormData] = useState({
    date: '',
    name: '',
    type: 'national',
    notes: ''
  })

  const queryClient = useQueryClient()

  const { data: holidays = [], isLoading } = useQuery({
    queryKey: ['holidays', selectedYear],
    queryFn: async () => {
      const response = await api.get('/holidays', { params: { year: selectedYear } })
      return response.data
    }
  })

  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await api.post('/holidays', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['holidays'])
      setIsCreating(false)
      resetForm()
    }
  })

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await api.put(`/holidays/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['holidays'])
      setEditingId(null)
      resetForm()
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      await api.delete(`/holidays/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['holidays'])
    }
  })

  const resetForm = () => {
    setFormData({
      date: '',
      name: '',
      type: 'national',
      notes: ''
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (editingId) {
      updateMutation.mutate({ id: editingId, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEdit = (holiday) => {
    setEditingId(holiday.id)
    setFormData({
      date: holiday.date,
      name: holiday.name,
      type: holiday.type,
      notes: holiday.notes || ''
    })
    setIsCreating(true)
  }

  const handleCancel = () => {
    setIsCreating(false)
    setEditingId(null)
    resetForm()
  }

  const getTypeLabel = (type) => {
    const types = {
      national: 'Nacional',
      local: 'Local',
      special_event: 'Evento Especial'
    }
    return types[type] || type
  }

  const getTypeColor = (type) => {
    const colors = {
      national: 'bg-red-100 text-red-800',
      local: 'bg-blue-100 text-blue-800',
      special_event: 'bg-purple-100 text-purple-800'
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 1 + i)

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <Calendar className="h-8 w-8" />
          Gestión de Feriados
        </h1>
        <p className="text-gray-600 mt-2">
          Configure los días feriados que aplican multiplicadores en el cálculo de costos
        </p>
      </div>

      {/* Filtro por año y botón crear */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700">Año:</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {years.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
            <span className="text-sm text-gray-600">
              {holidays.length} feriado{holidays.length !== 1 ? 's' : ''}
            </span>
          </div>
          {!isCreating && (
            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >
              <Plus className="h-5 w-5" />
              Agregar Feriado
            </button>
          )}
        </div>
      </div>

      {/* Formulario de creación/edición */}
      {isCreating && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">
            {editingId ? 'Editar Feriado' : 'Nuevo Feriado'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha *
                </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo *
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="national">Nacional</option>
                  <option value="local">Local</option>
                  <option value="special_event">Evento Especial</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                placeholder="Ej: Día de la Independencia"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notas
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={2}
                placeholder="Notas adicionales (opcional)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50"
              >
                <Save className="h-5 w-5" />
                {editingId ? 'Guardar Cambios' : 'Crear Feriado'}
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                <X className="h-5 w-5" />
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Lista de feriados */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Cargando feriados...</div>
        ) : holidays.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No hay feriados configurados para {selectedYear}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nombre
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tipo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Notas
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {holidays.map((holiday) => (
                  <tr key={holiday.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {format(parseISO(holiday.date), 'dd/MM/yyyy', { locale: es })}
                      </div>
                      <div className="text-xs text-gray-500">
                        {format(parseISO(holiday.date), 'EEEE', { locale: es })}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{holiday.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getTypeColor(holiday.type)}`}>
                        {getTypeLabel(holiday.type)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500 max-w-xs truncate">
                        {holiday.notes || '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleEdit(holiday)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                        title="Editar"
                      >
                        <Edit2 className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => {
                          if (window.confirm('¿Está seguro de eliminar este feriado?')) {
                            deleteMutation.mutate(holiday.id)
                          }
                        }}
                        className="text-red-600 hover:text-red-900"
                        title="Eliminar"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Información adicional */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">ℹ️ Información</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Los feriados aplican el <strong>multiplicador de feriados</strong> configurado en cada puesto de trabajo</li>
          <li>• Los domingos aplican el <strong>multiplicador de fin de semana</strong> automáticamente</li>
          <li>• Si un día es feriado Y domingo, se aplica el multiplicador de feriado (tiene prioridad)</li>
          <li>• Los multiplicadores se configuran en el módulo de <strong>Puestos de Trabajo</strong></li>
        </ul>
      </div>
    </div>
  )
}

export default HolidaysPage
