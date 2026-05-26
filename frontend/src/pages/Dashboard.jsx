import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { timeTrackingService } from '@/services/timeTrackingService'
import { employeeScheduleService } from '@/services/employeeScheduleService'
import { reportsService } from '@/services/reportsService'
import employeeService from '@/services/employeeService'
import configService from '@/services/configService'
import { Clock, Calendar, AlertCircle, TrendingUp, Users, DollarSign, TrendingDown } from 'lucide-react'

const Dashboard = () => {
  const { user, isAdmin } = useAuth()
  const [todayRecord, setTodayRecord] = useState(null)
  const [upcomingShift, setUpcomingShift] = useState(null)
  const [weeklyHours, setWeeklyHours] = useState(0)
  const [scheduledHours, setScheduledHours] = useState(40)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Estados para dashboard de administrador
  const [dashboardData, setDashboardData] = useState({
    ventas: { total: 0, cantidad: 0 },
    gastos: { total: 0 },
    rentabilidad: { resultado_neto: 0 }
  })
  const [activeEmployees, setActiveEmployees] = useState(0)

  // Estado para configuración de branding (logo y fondo del banner)
  const [brandingConfig, setBrandingConfig] = useState({
    logo_path: null,
    banner_background_path: null
  })

  useEffect(() => {
    if (!isAdmin()) {
      loadEmployeeDashboard()
    } else {
      loadAdminDashboard()
    }
  }, [user])

  useEffect(() => {
    const fetchBrandingConfig = async () => {
      try {
        const config = await configService.getBrandingConfig()
        setBrandingConfig(config)
      } catch (error) {
        console.error('Error loading branding config:', error)
      }
    }

    fetchBrandingConfig()
  }, [])

  const loadAdminDashboard = async () => {
    try {
      setLoading(true)
      setError(null)

      // Cargar datos del día (ventas hoy)
      const todayData = await reportsService.getDashboard('diario')
      
      // Cargar datos del mes (gastos del mes)
      const monthData = await reportsService.getDashboard('mensual')

      // Combinar datos: ventas del día, gastos del mes, balance del mes
      setDashboardData({
        ventas: todayData.ventas,
        gastos: monthData.gastos,
        rentabilidad: monthData.rentabilidad
      })

      // Cargar empleados activos
      const employeesData = await employeeService.getEmployees({ status: 'activo', limit: 1 })
      setActiveEmployees(employeesData.total || 0)
    } catch (err) {
      console.error('Error loading admin dashboard:', err)
      setError('Error al cargar información del dashboard')
    } finally {
      setLoading(false)
    }
  }

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

      // Cargar horas trabajadas de la semana actual (desde time tracking)
      const workedHours = await timeTrackingService.getCurrentWeekWorked()
      if (workedHours && workedHours.total_hours_decimal !== undefined) {
        setWeeklyHours(workedHours.total_hours_decimal)
      }

      // Cargar horas programadas de la semana actual (desde schedule)
      const currentWeek = await employeeScheduleService.getMyCurrentWeek()
      if (currentWeek && currentWeek.total_hours) {
        setScheduledHours(currentWeek.total_hours)
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

  const isShiftInProgress = (shift) => {
    if (!shift || !shift.shift_date || !shift.start_time) return false
    
    const today = new Date()
    const [year, month, day] = shift.shift_date.split('-').map(Number)
    const shiftDate = new Date(year, month - 1, day)
    
    // Check if shift is today
    if (shiftDate.toDateString() !== today.toDateString()) return false
    
    // Parse shift start time
    const [startHour, startMin] = shift.start_time.split(':').map(Number)
    
    const currentMinutes = today.getHours() * 60 + today.getMinutes()
    const startMinutes = startHour * 60 + startMin
    
    // Shift is in progress if current time is after start time and it's today
    // We check if there's an end_time in the shift schedule to verify we haven't passed it
    if (shift.end_time) {
      const [endHour, endMin] = shift.end_time.split(':').map(Number)
      const endMinutes = endHour * 60 + endMin
      return currentMinutes >= startMinutes && currentMinutes <= endMinutes
    }
    
    // If no end_time, just check if we've passed the start time
    return currentMinutes >= startMinutes
  }

  // Main Dashboard with Hero Banner
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Banner */}
      <div
        className="h-[20vh] w-full flex flex-col items-center justify-center relative"
        style={{
          backgroundImage: brandingConfig.banner_background_path
            ? `url('${brandingConfig.banner_background_path}')`
            : 'none',
          backgroundColor: brandingConfig.banner_background_path ? 'transparent' : 'white',
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        {/* Overlay to ensure logo is visible */}
        {brandingConfig.banner_background_path && (
          <div className="absolute inset-0 bg-black/20"></div>
        )}

        <div className="relative z-10 flex flex-col items-center">
          {brandingConfig.logo_path ? (
            <img
              src={brandingConfig.logo_path}
              alt="Galia Logo"
              className="h-[14vh] object-contain"
            />
          ) : (
            <h1 className="text-4xl md:text-5xl font-bold text-primary">Galia</h1>
          )}
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-red-900">{error}</p>
            </div>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Cargando...</p>
          </div>
        ) : (
          <>
            {!isAdmin() ? (
              // Employee Dashboard
              <div className="space-y-4 md:space-y-6">
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Mi Dashboard</h1>

                <>
                  {/* Próximo Turno */}
                  {upcomingShift ? (
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                          <h2 className="text-lg md:text-xl font-semibold text-gray-900">Próximo Turno</h2>
                          {isShiftInProgress(upcomingShift) && (
                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full">
                              En curso
                            </span>
                          )}
                        </div>
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
                          {todayRecord?.work_blocks && todayRecord.work_blocks.length > 0
                            ? formatTime(todayRecord.work_blocks[0].start_time)
                            : '—'}
                        </p>
                      </div>

                      <div className="bg-green-50 rounded-lg p-3 md:p-4">
                        <p className="text-xs md:text-sm text-gray-600 mb-1">Salida</p>
                        <p className="text-xl md:text-2xl font-bold text-green-600">
                          {todayRecord?.work_blocks && todayRecord.work_blocks.length > 0
                            ? (todayRecord.work_blocks[todayRecord.work_blocks.length - 1].end_time !==
                               todayRecord.work_blocks[todayRecord.work_blocks.length - 1].start_time
                                ? formatTime(todayRecord.work_blocks[todayRecord.work_blocks.length - 1].end_time)
                                : '—')
                            : '—'}
                        </p>
                      </div>

                      <div className="bg-purple-50 rounded-lg p-3 md:p-4">
                        <p className="text-xs md:text-sm text-gray-600 mb-1">Horas</p>
                        <p className="text-xl md:text-2xl font-bold text-purple-600">
                          {todayRecord?.total_hours !== undefined && todayRecord.total_hours > 0
                            ? `${todayRecord.total_hours}h ${todayRecord.total_minutes || 0}m`
                            : '0h'}
                        </p>
                      </div>
                    </div>

                    {todayRecord?.work_blocks && todayRecord.work_blocks.length > 0 &&
                     todayRecord.work_blocks[todayRecord.work_blocks.length - 1].end_time ===
                     todayRecord.work_blocks[todayRecord.work_blocks.length - 1].start_time && (
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
                        style={{ width: `${Math.min((weeklyHours / scheduledHours) * 100, 100)}%` }}
                      ></div>
                    </div>
                    <p className="text-xs md:text-sm text-gray-500 mt-2">
                      Meta: {scheduledHours.toFixed(1)} horas/semana
                    </p>
                  </div>
                </>
              </div>
            ) : (
              // Admin Dashboard
              <div className="space-y-4 md:space-y-6">
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Dashboard</h1>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-6">
                  <div className="bg-white p-4 md:p-6 rounded-lg shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-xs md:text-sm font-medium text-gray-500">Ventas Hoy</h3>
                        <p className="text-xl md:text-2xl font-bold text-gray-900 mt-2">
                          ${dashboardData.ventas?.total?.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) || '0'}
                        </p>
                      </div>
                      <DollarSign className="text-green-600" size={24} />
                    </div>
                  </div>
                  <div className="bg-white p-4 md:p-6 rounded-lg shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-xs md:text-sm font-medium text-gray-500">Empleados Activos</h3>
                        <p className="text-xl md:text-2xl font-bold text-gray-900 mt-2">{activeEmployees}</p>
                      </div>
                      <Users className="text-blue-600" size={24} />
                    </div>
                  </div>
                  <div className="bg-white p-4 md:p-6 rounded-lg shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-xs md:text-sm font-medium text-gray-500">Gastos del Mes</h3>
                        <p className="text-xl md:text-2xl font-bold text-gray-900 mt-2">
                          ${dashboardData.gastos?.total?.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) || '0'}
                        </p>
                      </div>
                      <TrendingDown className="text-red-600" size={24} />
                    </div>
                  </div>
                  <div className="bg-white p-4 md:p-6 rounded-lg shadow-sm border border-gray-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-xs md:text-sm font-medium text-gray-500">Balance</h3>
                        <p className="text-xl md:text-2xl font-bold text-gray-900 mt-2">
                          ${dashboardData.rentabilidad?.resultado_neto?.toLocaleString('es-AR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) || '0'}
                        </p>
                      </div>
                      <TrendingUp className="text-indigo-600" size={24} />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default Dashboard
