import { useQuery } from '@tanstack/react-query'
import { format, eachDayOfInterval, parseISO, startOfWeek, endOfWeek } from 'date-fns'
import { es } from 'date-fns/locale'
import { Users, TrendingUp, Clock } from 'lucide-react'
import api from '@/services/api'

const CoverageCalendar = ({ startDate, endDate }) => {
  const { data: coverage, isLoading } = useQuery({
    queryKey: ['coverage', startDate, endDate],
    queryFn: async () => {
      const response = await api.get('/coverage/hourly', {
        params: { start_date: startDate, end_date: endDate }
      })
      return response.data
    },
    enabled: !!startDate && !!endDate
  })

  const { data: summary } = useQuery({
    queryKey: ['coverage-summary', startDate, endDate],
    queryFn: async () => {
      const response = await api.get('/coverage/summary', {
        params: { start_date: startDate, end_date: endDate }
      })
      return response.data
    },
    enabled: !!startDate && !!endDate
  })

  if (isLoading) {
    return <div className="text-center p-8">Cargando cobertura...</div>
  }

  if (!coverage || coverage.length === 0) {
    return (
      <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No hay datos de cobertura para este período</p>
      </div>
    )
  }

  const getColorForCount = (count) => {
    if (count === 0) return 'bg-gray-100 text-gray-400'
    if (count === 1) return 'bg-yellow-100 text-yellow-800'
    if (count === 2) return 'bg-green-100 text-green-800'
    return 'bg-blue-100 text-blue-800'
  }

  const businessHours = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

  return (
    <div className="space-y-6">
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center space-x-2 text-gray-600 mb-2">
              <Users className="h-5 w-5" />
              <span className="text-sm font-medium">Total Turnos</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{summary.total_shifts}</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center space-x-2 text-gray-600 mb-2">
              <Clock className="h-5 w-5" />
              <span className="text-sm font-medium">Total Horas</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{summary.total_hours}h</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center space-x-2 text-gray-600 mb-2">
              <TrendingUp className="h-5 w-5" />
              <span className="text-sm font-medium">Hora Pico</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {summary.peak_hour !== null ? `${summary.peak_hour}:00` : 'N/A'}
            </p>
            <p className="text-xs text-gray-500">{summary.peak_hour_count} empleados</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <div className="flex items-center space-x-2 text-gray-600 mb-2">
              <Users className="h-5 w-5" />
              <span className="text-sm font-medium">Empleados Únicos</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{summary.unique_employees}</p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Cobertura por Hora</h3>
          <p className="text-sm text-gray-500 mt-1">Cantidad de empleados por hora del día</p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 sticky left-0 bg-gray-50">
                  Fecha
                </th>
                {businessHours.map((hour) => (
                  <th key={hour} className="px-2 py-3 text-center text-sm font-semibold text-gray-900 min-w-[60px]">
                    {hour}:00
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {coverage.map((dayData) => (
                <tr key={dayData.date} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 sticky left-0 bg-white">
                    <div>{format(parseISO(dayData.date), 'EEE', { locale: es })}</div>
                    <div className="text-xs text-gray-500">{format(parseISO(dayData.date), 'dd/MM')}</div>
                  </td>
                  {businessHours.map((hour) => {
                    const hourData = dayData.hourly_coverage.find(h => h.hour === hour)
                    const count = hourData?.employee_count || 0
                    return (
                      <td key={hour} className="px-2 py-3 text-center">
                        <div className={`inline-flex items-center justify-center w-10 h-10 rounded-lg font-semibold ${getColorForCount(count)}`}>
                          {count || '-'}
                        </div>
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-gray-100 border border-gray-300"></div>
              <span className="text-gray-600">Sin cobertura</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-yellow-100 border border-yellow-300"></div>
              <span className="text-gray-600">1 empleado</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-green-100 border border-green-300"></div>
              <span className="text-gray-600">2 empleados</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-blue-100 border border-blue-300"></div>
              <span className="text-gray-600">3+ empleados</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CoverageCalendar
