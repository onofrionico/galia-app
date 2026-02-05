import { useState } from 'react'
import { X, Calendar, Plus, Brain } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { format, addDays, startOfWeek, endOfWeek } from 'date-fns'
import { es } from 'date-fns/locale'
import api from '@/services/api'
import MLRecommendations from './MLRecommendations'
import { scheduleService } from '@/services/scheduleService'

const CreateScheduleModal = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient()
  const [startDate, setStartDate] = useState(format(startOfWeek(new Date(), { weekStartsOn: 1 }), 'yyyy-MM-dd'))
  const [endDate, setEndDate] = useState(format(endOfWeek(new Date(), { weekStartsOn: 1 }), 'yyyy-MM-dd'))
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: scheduleService.createSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries(['schedules'])
      onClose()
      setError('')
    },
    onError: (error) => {
      setError(error.response?.data?.error || 'Error al crear la grilla')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    if (new Date(endDate) < new Date(startDate)) {
      setError('La fecha de fin debe ser posterior a la fecha de inicio')
      return
    }

    createMutation.mutate({
      start_date: startDate,
      end_date: endDate,
    })
  }

  const setWeekDates = () => {
    const start = startOfWeek(new Date(), { weekStartsOn: 1 })
    const end = endOfWeek(new Date(), { weekStartsOn: 1 })
    setStartDate(format(start, 'yyyy-MM-dd'))
    setEndDate(format(end, 'yyyy-MM-dd'))
  }

  const setNextWeekDates = () => {
    const start = startOfWeek(addDays(new Date(), 7), { weekStartsOn: 1 })
    const end = endOfWeek(addDays(new Date(), 7), { weekStartsOn: 1 })
    setStartDate(format(start, 'yyyy-MM-dd'))
    setEndDate(format(end, 'yyyy-MM-dd'))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Nueva Grilla Horaria</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div className="flex space-x-2 mb-4">
            <button
              type="button"
              onClick={() => handleQuickFill('this_week')}
              className="text-sm text-primary hover:text-primary-dark flex items-center space-x-1"
            >
              <Plus className="h-4 w-4" />
              <span>Esta semana</span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill('next_week')}
              className="text-sm text-primary hover:text-primary-dark flex items-center space-x-1"
            >
              <Plus className="h-4 w-4" />
              <span>Próxima semana</span>
            </button>
          </div>

          {startDate && endDate && (
            <div className="space-y-3">
              <button
                type="button"
                onClick={() => setShowRecommendations(!showRecommendations)}
                className="w-full flex items-center justify-between px-4 py-3 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-lg transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <Brain className="h-5 w-5 text-purple-600" />
                  <span className="font-medium text-purple-900">
                    {showRecommendations ? 'Ocultar' : 'Ver'} Recomendaciones IA
                  </span>
                </div>
                <span className="text-xs bg-purple-600 text-white px-2 py-1 rounded">
                  ML
                </span>
              </button>

              {showRecommendations && (
                <MLRecommendations
                  startDate={startDate}
                  endDate={endDate}
                />
              )}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fecha de inicio
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fecha de fin
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              required
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createMutation.isPending ? 'Creando...' : 'Crear Grilla'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateScheduleModal
