import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { scheduleService } from '@/services/scheduleService'
import { X } from 'lucide-react'

const AddShiftModal = ({ isOpen, onClose, scheduleId, date, employee }) => {
  const queryClient = useQueryClient()
  const [startTime, setStartTime] = useState('09:00')
  const [endTime, setEndTime] = useState('17:00')
  const [error, setError] = useState('')

  const createShiftMutation = useMutation({
    mutationFn: scheduleService.createShift,
    onSuccess: () => {
      queryClient.invalidateQueries(['schedule', scheduleId])
      queryClient.invalidateQueries(['schedule-summary', scheduleId])
      onClose()
      setError('')
    },
    onError: (error) => {
      setError(error.response?.data?.error || 'Error al crear el turno')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    if (startTime >= endTime) {
      setError('La hora de fin debe ser posterior a la hora de inicio')
      return
    }

    createShiftMutation.mutate({
      schedule_id: scheduleId,
      employee_id: employee.id,
      shift_date: date,
      start_time: startTime,
      end_time: endTime,
    })
  }

  const setMorningShift = () => {
    setStartTime('08:00')
    setEndTime('14:00')
  }

  const setAfternoonShift = () => {
    setStartTime('14:00')
    setEndTime('20:00')
  }

  const setFullDayShift = () => {
    setStartTime('09:00')
    setEndTime('18:00')
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Agregar Turno</h2>
            <p className="text-sm text-gray-500 mt-1">
              {employee.full_name} - {date}
            </p>
          </div>
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
              onClick={setMorningShift}
              className="flex-1 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Mañana (8-14)
            </button>
            <button
              type="button"
              onClick={setAfternoonShift}
              className="flex-1 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Tarde (14-20)
            </button>
            <button
              type="button"
              onClick={setFullDayShift}
              className="flex-1 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Completo (9-18)
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Hora de inicio
            </label>
            <input
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Hora de fin
            </label>
            <input
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              required
            />
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              Duración estimada: {calculateHours(startTime, endTime)} horas
            </p>
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
              disabled={createShiftMutation.isPending}
              className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createShiftMutation.isPending ? 'Creando...' : 'Agregar Turno'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function calculateHours(start, end) {
  const [startHour, startMin] = start.split(':').map(Number)
  const [endHour, endMin] = end.split(':').map(Number)
  
  let hours = endHour - startHour
  let minutes = endMin - startMin
  
  if (minutes < 0) {
    hours -= 1
    minutes += 60
  }
  
  if (hours < 0) {
    hours += 24
  }
  
  return hours + (minutes / 60).toFixed(2)
}

export default AddShiftModal
