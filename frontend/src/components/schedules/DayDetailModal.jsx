import { useQuery } from '@tanstack/react-query'
import { format, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'
import { X, Clock, User, ChevronRight } from 'lucide-react'
import api from '@/services/api'

const DayDetailModal = ({ date, filters, onClose }) => {
  const { data: dayDetail, isLoading } = useQuery({
    queryKey: ['day-detail', date, filters.employee_id, filters.shift_schedule_id],
    queryFn: async () => {
      const params = { date }
      if (filters.employee_id) params.employee_id = filters.employee_id
      if (filters.shift_schedule_id) params.shift_schedule_id = filters.shift_schedule_id
      
      const response = await api.get('/time-tracking/calendar/day-detail', { params })
      return response.data
    },
    enabled: !!date
  })

  const formatHour = (hour) => {
    return `${hour.toString().padStart(2, '0')}:00`
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Detalle del Día
            </h2>
            <p className="text-sm text-gray-600 capitalize">
              {format(parseISO(date), "EEEE, d 'de' MMMM 'de' yyyy", { locale: es })}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {isLoading ? (
            <div className="text-center p-8 text-gray-500">Cargando detalle...</div>
          ) : !dayDetail || dayDetail.total_employees === 0 ? (
            <div className="text-center p-8 text-gray-500">
              No hay registros de horas trabajadas para este día
            </div>
          ) : (
            <div className="space-y-6">
              {/* Resumen de empleados */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <User className="h-5 w-5 mr-2 text-primary" />
                  Empleados ({dayDetail.total_employees})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {dayDetail.employees_summary.map((employee) => (
                    <div
                      key={employee.employee_id}
                      className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-gray-900">
                          {employee.employee_name}
                        </span>
                        <span className="text-sm font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                          {employee.total_hours}h {employee.total_minutes > 0 && `${employee.total_minutes}m`}
                        </span>
                      </div>
                      <div className="space-y-1">
                        {employee.work_blocks.map((block, idx) => (
                          <div key={idx} className="flex items-center text-sm text-gray-600">
                            <Clock className="h-3.5 w-3.5 mr-1.5 text-gray-400" />
                            <span>{block.start_time}</span>
                            <ChevronRight className="h-3 w-3 mx-1" />
                            <span>{block.end_time}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Desglose por hora */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <Clock className="h-5 w-5 mr-2 text-primary" />
                  Desglose por Hora
                </h3>
                <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                          Hora
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">
                          Empleados Trabajando
                        </th>
                        <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900">
                          Cantidad
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {Object.entries(dayDetail.hours_breakdown)
                        .sort(([a], [b]) => parseInt(a) - parseInt(b))
                        .map(([hour, employees]) => (
                          <tr key={hour} className="hover:bg-white transition-colors">
                            <td className="px-4 py-3">
                              <span className="font-mono text-sm font-medium text-gray-900">
                                {formatHour(parseInt(hour))}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex flex-wrap gap-2">
                                {employees.map((emp, idx) => (
                                  <span
                                    key={idx}
                                    className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                                  >
                                    {emp.employee_name}
                                    <span className="ml-1 text-blue-600">
                                      ({emp.start_time}-{emp.end_time})
                                    </span>
                                  </span>
                                ))}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white font-semibold">
                                {employees.length}
                              </span>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors font-medium"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}

export default DayDetailModal
