import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { scheduleService } from '@/services/scheduleService'
import employeeService from '@/services/employeeService'
import { format, eachDayOfInterval, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'
import { Plus, Trash2, Clock, DollarSign, Send } from 'lucide-react'
import AddShiftModal from './AddShiftModal'

const ScheduleGrid = ({ schedule, onBack }) => {
  const queryClient = useQueryClient()
  const [showAddShift, setShowAddShift] = useState(false)
  const [selectedDate, setSelectedDate] = useState(null)
  const [selectedEmployee, setSelectedEmployee] = useState(null)

  const { data: scheduleData, isLoading } = useQuery({
    queryKey: ['schedule', schedule.id],
    queryFn: () => scheduleService.getSchedule(schedule.id),
  })

  const { data: employeesData } = useQuery({
    queryKey: ['employees'],
    queryFn: employeeService.getEmployees,
  })
  
  const employees = employeesData?.employees || []

  const { data: summary } = useQuery({
    queryKey: ['schedule-summary', schedule.id],
    queryFn: () => scheduleService.getScheduleSummary(schedule.id),
  })

  const deleteShiftMutation = useMutation({
    mutationFn: scheduleService.deleteShift,
    onSuccess: () => {
      queryClient.invalidateQueries(['schedule', schedule.id])
      queryClient.invalidateQueries(['schedule-summary', schedule.id])
    },
  })

  const publishMutation = useMutation({
    mutationFn: () => scheduleService.publishSchedule(schedule.id),
    onSuccess: () => {
      queryClient.invalidateQueries(['schedule', schedule.id])
      queryClient.invalidateQueries(['schedules'])
    },
  })

  if (isLoading) {
    return <div className="p-8 text-center">Cargando...</div>
  }

  const dates = eachDayOfInterval({
    start: parseISO(scheduleData.start_date),
    end: parseISO(scheduleData.end_date),
  })

  const getShiftsForEmployeeAndDate = (employeeId, date) => {
    return scheduleData.shifts?.filter(
      (shift) =>
        shift.employee_id === employeeId &&
        shift.shift_date === format(date, 'yyyy-MM-dd')
    ) || []
  }

  const handleAddShift = (date, employee) => {
    setSelectedDate(format(date, 'yyyy-MM-dd'))
    setSelectedEmployee(employee)
    setShowAddShift(true)
  }

  const handleDeleteShift = (shiftId) => {
    if (window.confirm('¿Estás seguro de eliminar este turno?')) {
      deleteShiftMutation.mutate(shiftId)
    }
  }

  const handlePublish = () => {
    if (window.confirm('¿Estás seguro de publicar esta grilla? Los empleados podrán verla.')) {
      publishMutation.mutate()
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={onBack}
            className="text-primary hover:text-primary/80 mb-2"
          >
            ← Volver a grillas
          </button>
          <h2 className="text-2xl font-bold text-gray-900">
            Grilla: {format(parseISO(scheduleData.start_date), 'dd MMM', { locale: es })} - {format(parseISO(scheduleData.end_date), 'dd MMM yyyy', { locale: es })}
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Estado: <span className={scheduleData.status === 'published' ? 'text-green-600 font-semibold' : 'text-yellow-600 font-semibold'}>
              {scheduleData.status === 'published' ? 'Publicada' : 'Borrador'}
            </span>
          </p>
        </div>
        {scheduleData.status === 'draft' && (
          <button
            onClick={handlePublish}
            disabled={publishMutation.isPending}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
            <span>{publishMutation.isPending ? 'Publicando...' : 'Publicar Grilla'}</span>
          </button>
        )}
      </div>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center space-x-2 text-gray-600 mb-2">
              <Clock className="h-5 w-5" />
              <span className="text-sm font-medium">Horas Totales</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {summary.hours_summary.reduce((acc, emp) => acc + emp.total_hours, 0).toFixed(2)}h
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center space-x-2 text-gray-600 mb-2">
              <DollarSign className="h-5 w-5" />
              <span className="text-sm font-medium">Costo Total</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              ${summary.cost_summary.total_cost.toFixed(2)}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center space-x-2 text-gray-600 mb-2">
              <Clock className="h-5 w-5" />
              <span className="text-sm font-medium">Turnos</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {scheduleData.shifts?.length || 0}
            </p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 sticky left-0 bg-gray-50 z-10">
                Empleado
              </th>
              {dates.map((date) => (
                <th key={date.toISOString()} className="px-4 py-3 text-center text-sm font-semibold text-gray-900 min-w-[150px]">
                  <div>{format(date, 'EEE', { locale: es })}</div>
                  <div className="text-xs font-normal text-gray-500">{format(date, 'dd/MM')}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {employees?.map((employee) => (
              <tr key={employee.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                  {employee.full_name}
                </td>
                {dates.map((date) => {
                  const shifts = getShiftsForEmployeeAndDate(employee.id, date)
                  return (
                    <td key={date.toISOString()} className="px-2 py-2 text-center">
                      <div className="space-y-1">
                        {shifts.map((shift) => (
                          <div
                            key={shift.id}
                            className="bg-primary/10 border border-primary/30 rounded px-2 py-1 text-xs group relative"
                          >
                            <div className="font-medium text-primary">
                              {shift.start_time.substring(0, 5)} - {shift.end_time.substring(0, 5)}
                            </div>
                            <div className="text-gray-600">{shift.hours}h</div>
                            <button
                              onClick={() => handleDeleteShift(shift.id)}
                              className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                              title={scheduleData.status === 'published' ? 'El empleado será notificado' : 'Eliminar turno'}
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                        ))}
                        <button
                          onClick={() => handleAddShift(date, employee)}
                          className="w-full py-1 text-xs text-gray-400 hover:text-primary hover:bg-primary/5 rounded transition-colors"
                          title={scheduleData.status === 'published' ? 'El empleado será notificado del nuevo turno' : 'Agregar turno'}
                        >
                          <Plus className="h-4 w-4 mx-auto" />
                        </button>
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showAddShift && (
        <AddShiftModal
          isOpen={showAddShift}
          onClose={() => {
            setShowAddShift(false)
            setSelectedDate(null)
            setSelectedEmployee(null)
          }}
          scheduleId={schedule.id}
          date={selectedDate}
          employee={selectedEmployee}
        />
      )}
    </div>
  )
}

export default ScheduleGrid
