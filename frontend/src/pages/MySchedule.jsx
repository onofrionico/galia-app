import { useState, useEffect } from 'react'
import { employeeScheduleService } from '../services/employeeScheduleService'
import { Calendar, Clock, ChevronLeft, ChevronRight } from 'lucide-react'
import WeeklyScheduleView from '../components/schedules/WeeklyScheduleView'
import MonthlyScheduleView from '../components/schedules/MonthlyScheduleView'

const MySchedule = () => {
  const [view, setView] = useState('weekly')
  const [weeklySchedule, setWeeklySchedule] = useState(null)
  const [monthlySchedule, setMonthlySchedule] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentDate, setCurrentDate] = useState(new Date())

  useEffect(() => {
    loadSchedule()
  }, [view, currentDate])

  const loadSchedule = async () => {
    setLoading(true)
    setError(null)
    
    try {
      if (view === 'weekly') {
        const startDate = getWeekStart(currentDate)
        const data = await employeeScheduleService.getMyWeeklySchedule(startDate.toISOString().split('T')[0])
        setWeeklySchedule(data)
      } else {
        const year = currentDate.getFullYear()
        const month = currentDate.getMonth() + 1
        const data = await employeeScheduleService.getMyMonthlySchedule(year, month)
        setMonthlySchedule(data)
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar el horario')
    } finally {
      setLoading(false)
    }
  }

  const getWeekStart = (date) => {
    const d = new Date(date)
    const day = d.getDay()
    const diff = d.getDate() - day + (day === 0 ? -6 : 1)
    return new Date(d.setDate(diff))
  }

  const navigatePrevious = () => {
    const newDate = new Date(currentDate)
    if (view === 'weekly') {
      newDate.setDate(newDate.getDate() - 7)
    } else {
      newDate.setMonth(newDate.getMonth() - 1)
    }
    setCurrentDate(newDate)
  }

  const navigateNext = () => {
    const newDate = new Date(currentDate)
    if (view === 'weekly') {
      newDate.setDate(newDate.getDate() + 7)
    } else {
      newDate.setMonth(newDate.getMonth() + 1)
    }
    setCurrentDate(newDate)
  }

  const navigateToday = () => {
    setCurrentDate(new Date())
  }

  const getDisplayTitle = () => {
    if (view === 'weekly') {
      const weekStart = getWeekStart(currentDate)
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekEnd.getDate() + 6)
      
      return `${weekStart.toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })} - ${weekEnd.toLocaleDateString('es-AR', { day: 'numeric', month: 'long', year: 'numeric' })}`
    } else {
      return currentDate.toLocaleDateString('es-AR', { month: 'long', year: 'numeric' })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Mi Horario</h1>
        
        <div className="flex gap-2">
          <button
            onClick={() => setView('weekly')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              view === 'weekly'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Semanal
            </div>
          </button>
          <button
            onClick={() => setView('monthly')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              view === 'monthly'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Mensual
            </div>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-6">
          <button
            onClick={navigatePrevious}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-gray-900 capitalize">
              {getDisplayTitle()}
            </h2>
            <button
              onClick={navigateToday}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Hoy
            </button>
          </div>
          
          <button
            onClick={navigateNext}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {!loading && !error && view === 'weekly' && weeklySchedule && (
          <WeeklyScheduleView schedule={weeklySchedule} />
        )}

        {!loading && !error && view === 'monthly' && monthlySchedule && (
          <MonthlyScheduleView schedule={monthlySchedule} />
        )}
      </div>
    </div>
  )
}

export default MySchedule
