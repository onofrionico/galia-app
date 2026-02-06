import { useState, useEffect } from 'react'
import { timeTrackingService } from '../../services/timeTrackingService'
import { Calendar, Clock, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react'

const WorkHistoryView = () => {
  const [view, setView] = useState('weekly')
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [currentDate, setCurrentDate] = useState(new Date())

  useEffect(() => {
    loadRecords()
  }, [view, currentDate])

  const loadRecords = async () => {
    setLoading(true)
    setError(null)

    try {
      if (view === 'weekly') {
        const weekStart = getWeekStart(currentDate)
        const weekEnd = new Date(weekStart)
        weekEnd.setDate(weekEnd.getDate() + 6)

        const startStr = weekStart.toISOString().split('T')[0]
        const endStr = weekEnd.toISOString().split('T')[0]

        const data = await timeTrackingService.getRecords(startStr, endStr)
        setRecords(data)
      } else {
        const year = currentDate.getFullYear()
        const month = currentDate.getMonth() + 1
        const data = await timeTrackingService.getMonthlyRecords(year, month)
        setRecords(data)
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar el historial')
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

  const calculateTotalHours = () => {
    let totalHours = 0
    let totalMinutes = 0

    records.forEach(record => {
      if (record.work_blocks && record.work_blocks.length > 0) {
        totalHours += record.total_hours || 0
        totalMinutes += record.total_minutes || 0
      }
    })

    totalHours += Math.floor(totalMinutes / 60)
    totalMinutes = totalMinutes % 60

    return { hours: totalHours, minutes: totalMinutes }
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

  const getDayName = (dateStr) => {
    const date = new Date(dateStr + 'T00:00:00')
    return date.toLocaleDateString('es-AR', { weekday: 'short' })
  }

  const formatTime = (time) => {
    if (!time) return '--:--'
    return time.substring(0, 5)
  }

  const totalHours = calculateTotalHours()

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Historial de Trabajo</h2>

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
            <h3 className="text-xl font-semibold text-gray-900 capitalize">
              {getDisplayTitle()}
            </h3>
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

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2 mb-4">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total de horas {view === 'weekly' ? 'esta semana' : 'este mes'}</p>
                  <p className="text-3xl font-bold text-blue-600">
                    {totalHours.hours}h {totalHours.minutes}m
                  </p>
                </div>
                <Clock className="w-12 h-12 text-blue-400 opacity-50" />
              </div>
            </div>

            {records.length === 0 ? (
              <div className="text-center py-8">
                <Clock className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No hay registros para este período</p>
              </div>
            ) : (
              <div className="space-y-3">
                {records.map((record) => (
                  <div
                    key={record.id}
                    className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-4">
                        <div className="text-center min-w-[80px]">
                          <p className="text-sm font-semibold text-gray-900 uppercase">
                            {getDayName(record.tracking_date)}
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(record.tracking_date + 'T00:00:00').toLocaleDateString('es-AR', {
                              day: 'numeric',
                              month: 'numeric'
                            })}
                          </p>
                        </div>
                      </div>

                      {record.work_blocks && record.work_blocks.length > 0 && (
                        <div className="text-right">
                          <p className="text-xs text-gray-500 mb-1">Total</p>
                          <p className="text-lg font-bold text-green-600">
                            {record.total_hours}h {record.total_minutes}m
                          </p>
                        </div>
                      )}

                      {(!record.work_blocks || record.work_blocks.length === 0) && (
                        <div className="text-right">
                          <span className="text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded">
                            Sin registros
                          </span>
                        </div>
                      )}
                    </div>

                    {record.work_blocks && record.work_blocks.length > 0 && (
                      <div className="space-y-2 pl-4">
                        {record.work_blocks.map((block, idx) => (
                          <div key={idx} className="flex items-center gap-3 text-sm">
                            <span className="text-gray-500">Bloque {idx + 1}:</span>
                            <span className="font-mono font-bold text-gray-900">
                              {formatTime(block.start_time)} - {formatTime(block.end_time)}
                            </span>
                            {block.start_time !== block.end_time && (
                              <span className="text-gray-500">
                                ({(() => {
                                  const [sHour, sMin] = block.start_time.split(':').map(Number)
                                  const [eHour, eMin] = block.end_time.split(':').map(Number)
                                  let h = eHour - sHour
                                  let m = eMin - sMin
                                  if (m < 0) {
                                    h--
                                    m += 60
                                  }
                                  return `${h}h ${m}m`
                                })()})
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default WorkHistoryView
