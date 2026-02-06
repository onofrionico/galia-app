import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { timeTrackingService } from '@/services/timeTrackingService'
import { employeeScheduleService } from '@/services/employeeScheduleService'
import { Clock, Calendar, AlertCircle, TrendingUp, Users, DollarSign, TrendingDown } from 'lucide-react'

const Dashboard = () => {
  const { user, isAdmin } = useAuth()
  const [todayRecord, setTodayRecord] = useState(null)
  const [upcomingShift, setUpcomingShift] = useState(null)
  const [weeklyHours, setWeeklyHours] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!isAdmin()) {
      loadEmployeeDashboard()
    } else {
      setLoading(false)
    }
  }, [user])

  const loadEmployeeDashboard = async () => {
    try {
      setLoading(true)
      setError(null)

      // Cargar registro de hoy
      const today = await timeTrackingService.getTodayRecord()
      setTodayRecord(today)

      // Cargar próximo turno
      const upcomingShiftsData = await employeeScheduleService.getMyUpcomingShifts(7)
      if (upcomingShiftsData && upcomingShiftsData.shifts && upcomingShiftsData.shifts.length > 0) {
        setUpcomingShift(upcomingShiftsData.shifts[0])
      }

      // Cargar horas de la semana actual
      const currentWeek = await employeeScheduleService.getMyCurrentWeek()
      if (currentWeek && currentWeek.total_hours) {
        setWeeklyHours(currentWeek.total_hours)
      }
    } catch (err) {
      console.error('Error loading employee dashboard:', err)
      setError('Error al cargar información del dashboard')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (timeStr) => {
    if (!timeStr) return 'N/A'
    return timeStr.substring(0, 5)
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    const [year, month, day] = dateStr.split('-').map(Number)
    const date = new Date(year, month - 1, day)
    return date.toLocaleDateString('es-AR', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  }

  // Dashboard para Empleados
  if (!isAdmin()) {
    return (
      <div className="space-y-4 md:space-y-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Mi Dashboard</h1>

        {error && (
          <div className="bg-yellow-50 border-l-4 border-yellow-500 p-3 md:p-4 flex items-start gap-3">
            <AlertCircle className="text-yellow-500 flex-shrink-0 mt-0.5" size={18} />
            <div className="text-xs md:text-sm text-yellow-700">{error}</div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <>
            {/* Próximo Turno */}
            {upcomingShift ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg md:text-xl font-semibold text-gray-900">Próximo Turno</h2>
                  <Calendar className="text-orange-600" size={24} />
                </div>

                <div className="space-y-3">
                  <div>
                    <p className="text-xs md:text-sm text-gray-600 mb-1">Fecha</p>
                    <p className="text-base md:text-lg font-semibold text-gray-900 capitalize">
                      {formatDate(upcomingShift.shift_date)}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-orange-50 rounded-lg p-3">
                      <p className="text-xs md:text-sm text-gray-600 mb-1">Inicio</p>
                      <p className="text-lg md:text-xl font-bold text-orange-600">
                        {upcomingShift.start_time ? formatTime(upcomingShift.start_time) : '—'}
                      </p>
                    </div>

                    <div className="bg-orange-50 rounded-lg p-3">
                      <p className="text-xs md:text-sm text-gray-600 mb-1">Fin</p>
                      <p className="text-lg md:text-xl font-bold text-orange-600">
                        {upcomingShift.end_time ? formatTime(upcomingShift.end_time) : '—'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6">
                <div className="flex items-center gap-3">
                  <AlertCircle className="text-gray-400" size={20} />
                  <p className="text-sm md:text-base text-gray-600">
                    No hay turnos próximos asignados
                  </p>
                </div>
              </div>
            )}

            {/* Horas Trabajadas Hoy */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg md:text-xl font-semibold text-gray-900">Hoy</h2>
                <Clock className="text-blue-600" size={24} />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4">
                <div className="bg-blue-50 rounded-lg p-3 md:p-4">
                  <p className="text-xs md:text-sm text-gray-600 mb-1">Entrada</p>
                  <p className="text-xl md:text-2xl font-bold text-blue-600">
                    {todayRecord?.check_in ? formatTime(todayRecord.check_in) : '—'}
                  </p>
                </div>

                <div className="bg-green-50 rounded-lg p-3 md:p-4">
                  <p className="text-xs md:text-sm text-gray-600 mb-1">Salida</p>
                  <p className="text-xl md:text-2xl font-bold text-green-600">
                    {todayRecord?.check_out ? formatTime(todayRecord.check_out) : '—'}
                  </p>
                </div>

                <div className="bg-purple-50 rounded-lg p-3 md:p-4">
                  <p className="text-xs md:text-sm text-gray-600 mb-1">Horas</p>
                  <p className="text-xl md:text-2xl font-bold text-purple-600">
                    {todayRecord?.hours_worked ? todayRecord.hours_worked.toFixed(1) : '0'}h
                  </p>
                </div>
              </div>

              {todayRecord?.check_in && !todayRecord?.check_out && (
                <div className="mt-4 p-3 bg-green-100 border border-green-300 rounded-lg">
                  <p className="text-xs md:text-sm text-green-800 font-medium">
                    ✓ Entrada registrada. No olvides registrar tu salida.
                  </p>
                </div>
              )}
            </div>

            {/* Horas de la Semana */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg md:text-xl font-semibold text-gray-900">Esta Semana</h2>
                <TrendingUp className="text-indigo-600" size={24} />
              </div>

              <div className="flex items-baseline gap-2">
                <p className="text-3xl md:text-4xl font-bold text-indigo-600">
                  {weeklyHours.toFixed(1)}
                </p>
                <p className="text-sm md:text-base text-gray-600">horas trabajadas</p>
              </div>

              <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-indigo-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min((weeklyHours / 40) * 100, 100)}%` }}
                ></div>
              </div>
              <p className="text-xs md:text-sm text-gray-500 mt-2">
                Meta: 40 horas/semana
              </p>
            </div>
          </>
        )}
      </div>
    )
  }

  // Dashboard para Administradores
  return (
    <div className="space-y-4 md:space-y-6">
      <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Dashboard</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-6">
        <div className="bg-white p-4 md:p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs md:text-sm font-medium text-gray-500">Ventas Hoy</h3>
              <p className="text-xl md:text-2xl font-bold text-gray-900 mt-2">$0</p>
            </div>
            <DollarSign className="text-green-600" size={24} />
          </div>
        </div>
        <div className="bg-white p-4 md:p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs md:text-sm font-medium text-gray-500">Empleados Activos</h3>
              <p className="text-xl md:text-2xl font-bold text-gray-900 mt-2">0</p>
            </div>
            <Users className="text-blue-600" size={24} />
          </div>
        </div>
        <div className="bg-white p-4 md:p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs md:text-sm font-medium text-gray-500">Gastos del Mes</h3>
              <p className="text-xl md:text-2xl font-bold text-gray-900 mt-2">$0</p>
            </div>
            <TrendingDown className="text-red-600" size={24} />
          </div>
        </div>
        <div className="bg-white p-4 md:p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs md:text-sm font-medium text-gray-500">Balance</h3>
              <p className="text-xl md:text-2xl font-bold text-gray-900 mt-2">$0</p>
            </div>
            <TrendingUp className="text-indigo-600" size={24} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
