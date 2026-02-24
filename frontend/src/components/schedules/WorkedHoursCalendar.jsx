import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  format, 
  startOfMonth, 
  endOfMonth, 
  eachDayOfInterval, 
  isSameMonth, 
  isSameDay,
  addMonths,
  subMonths,
  startOfWeek,
  endOfWeek,
  parseISO
} from 'date-fns'
import { es } from 'date-fns/locale'
import { ChevronLeft, ChevronRight, Clock, Users, Calendar, DollarSign } from 'lucide-react'
import api from '@/services/api'
import DayDetailModal from './DayDetailModal'

const WorkedHoursCalendar = ({ employees = [], schedules = [] }) => {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedDay, setSelectedDay] = useState(null)
  const [filters, setFilters] = useState({
    employee_id: '',
    shift_schedule_id: ''
  })

  const year = currentDate.getFullYear()
  const month = currentDate.getMonth() + 1

  const { data: calendarData, isLoading } = useQuery({
    queryKey: ['worked-hours-calendar', year, month, filters.employee_id, filters.shift_schedule_id],
    queryFn: async () => {
      const params = { year, month }
      if (filters.employee_id) params.employee_id = filters.employee_id
      if (filters.shift_schedule_id) params.shift_schedule_id = filters.shift_schedule_id
      
      const response = await api.get('/time-tracking/calendar', { params })
      return response.data
    },
    staleTime: 0,
    refetchOnMount: true
  })

  const monthStart = startOfMonth(currentDate)
  const monthEnd = endOfMonth(currentDate)
  const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 })
  const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 })
  const calendarDays = eachDayOfInterval({ start: calendarStart, end: calendarEnd })

  const getDayData = (day) => {
    if (!calendarData?.days) return null
    const dayStr = format(day, 'yyyy-MM-dd')
    return calendarData.days.find(d => d.date === dayStr)
  }

  const getHoursColor = (hours) => {
    if (hours === 0) return 'bg-gray-50'
    if (hours <= 4) return 'bg-blue-50'
    if (hours <= 8) return 'bg-blue-100'
    if (hours <= 16) return 'bg-blue-200'
    return 'bg-blue-300'
  }

  const formatHours = (hours, minutes) => {
    if (hours === 0 && minutes === 0) return '-'
    if (minutes === 0) return `${hours}h`
    return `${hours}h ${minutes}m`
  }

  const totalMonthHours = calendarData?.days?.reduce((acc, day) => {
    return acc + day.total_hours + (day.total_minutes / 60)
  }, 0) || 0

  const totalEmployeeDays = calendarData?.days?.reduce((acc, day) => {
    return acc + day.employee_count
  }, 0) || 0

  const daysWithWork = calendarData?.days?.filter(d => d.total_hours > 0 || d.total_minutes > 0).length || 0

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filtrar por Empleado
            </label>
            <select
              value={filters.employee_id}
              onChange={(e) => setFilters({ ...filters, employee_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm"
            >
              <option value="">Todos los empleados</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.full_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Filtrar por Grilla/Turno
            </label>
            <select
              value={filters.shift_schedule_id}
              onChange={(e) => setFilters({ ...filters, shift_schedule_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm"
            >
              <option value="">Todas las grillas</option>
              {schedules.map((schedule) => (
                <option key={schedule.id} value={schedule.id}>
                  {format(parseISO(schedule.start_date), 'dd/MM/yyyy')} - {format(parseISO(schedule.end_date), 'dd/MM/yyyy')}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Resumen del mes */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center space-x-2 text-gray-600 mb-2">
            <Clock className="h-5 w-5" />
            <span className="text-sm font-medium">Total Horas del Mes</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{totalMonthHours.toFixed(1)}h</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center space-x-2 text-gray-600 mb-2">
            <Users className="h-5 w-5" />
            <span className="text-sm font-medium">Registros de Empleados</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{totalEmployeeDays}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center space-x-2 text-gray-600 mb-2">
            <Calendar className="h-5 w-5" />
            <span className="text-sm font-medium">Días con Actividad</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{daysWithWork}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center space-x-2 text-gray-600 mb-2">
            <DollarSign className="h-5 w-5" />
            <span className="text-sm font-medium">Gasto Total del Mes</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            ${(calendarData?.total_cost ?? 0).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      {/* Calendario */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {/* Header con navegación */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <button
            onClick={() => setCurrentDate(subMonths(currentDate, 1))}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <h3 className="text-lg font-semibold text-gray-900 capitalize">
            {format(currentDate, 'MMMM yyyy', { locale: es })}
          </h3>
          <button
            onClick={() => setCurrentDate(addMonths(currentDate, 1))}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Cargando calendario...</div>
        ) : (
          <div className="p-4">
            {/* Días de la semana */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'].map((day) => (
                <div key={day} className="text-center text-sm font-semibold text-gray-600 py-2">
                  {day}
                </div>
              ))}
            </div>

            {/* Días del calendario */}
            <div className="grid grid-cols-7 gap-1">
              {calendarDays.map((day) => {
                const dayData = getDayData(day)
                const isCurrentMonth = isSameMonth(day, currentDate)
                const isToday = isSameDay(day, new Date())
                const hasWork = dayData && (dayData.total_hours > 0 || dayData.total_minutes > 0)

                return (
                  <button
                    key={day.toISOString()}
                    onClick={() => hasWork && setSelectedDay(format(day, 'yyyy-MM-dd'))}
                    disabled={!hasWork}
                    className={`
                      relative p-2 min-h-[80px] rounded-lg border transition-all text-left
                      ${isCurrentMonth ? 'bg-white' : 'bg-gray-50'}
                      ${hasWork ? 'cursor-pointer hover:border-primary hover:shadow-md' : 'cursor-default'}
                      ${isToday ? 'border-primary border-2' : 'border-gray-200'}
                      ${getHoursColor(dayData?.total_hours || 0)}
                    `}
                  >
                    <span className={`
                      text-sm font-medium
                      ${isCurrentMonth ? 'text-gray-900' : 'text-gray-400'}
                      ${isToday ? 'text-primary' : ''}
                    `}>
                      {format(day, 'd')}
                    </span>

                    {hasWork && isCurrentMonth && (
                      <div className="mt-1 space-y-0.5">
                        <div className="text-xs font-semibold text-blue-700">
                          {formatHours(dayData.total_hours, dayData.total_minutes)}
                        </div>
                        <div className="text-xs text-gray-500 flex items-center">
                          <Users className="h-3 w-3 mr-1" />
                          {dayData.employee_count}
                        </div>
                        {dayData.daily_cost > 0 && (
                          <div className="text-xs font-medium text-green-700">
                            ${dayData.daily_cost.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                          </div>
                        )}
                      </div>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Leyenda */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-gray-50 border border-gray-300"></div>
              <span className="text-gray-600">Sin registros</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-blue-50 border border-blue-200"></div>
              <span className="text-gray-600">1-4 horas</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-blue-100 border border-blue-300"></div>
              <span className="text-gray-600">5-8 horas</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-blue-200 border border-blue-400"></div>
              <span className="text-gray-600">9-16 horas</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-blue-300 border border-blue-500"></div>
              <span className="text-gray-600">16+ horas</span>
            </div>
          </div>
        </div>
      </div>

      {/* Modal de detalle del día */}
      {selectedDay && (
        <DayDetailModal
          date={selectedDay}
          filters={filters}
          onClose={() => setSelectedDay(null)}
        />
      )}
    </div>
  )
}

export default WorkedHoursCalendar
