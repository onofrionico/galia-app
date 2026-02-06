import { useState, useEffect } from 'react'
import { timeTrackingService } from '../services/timeTrackingService'
import { Clock, LogIn, LogOut, Calendar, AlertCircle } from 'lucide-react'
import WorkHistoryView from '../components/timeTracking/WorkHistoryView'

const TimeTracking = () => {
  const [todayRecord, setTodayRecord] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [showPastDayForm, setShowPastDayForm] = useState(false)
  const [pastDayData, setPastDayData] = useState({
    date: new Date().toISOString().split('T')[0],
    check_in: '09:00',
    check_out: '17:00'
  })

  useEffect(() => {
    loadTodayRecord()
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const loadTodayRecord = async () => {
    try {
      setError(null)
      const data = await timeTrackingService.getTodayRecord()
      setTodayRecord(data)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar el registro del día')
    }
  }

  const handleCheckIn = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await timeTrackingService.recordCheckIn(new Date().toISOString().split('T')[0])
      setTodayRecord(result.record)
      setSuccess('Entrada registrada exitosamente')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al registrar entrada')
    } finally {
      setLoading(false)
    }
  }

  const handleCheckOut = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await timeTrackingService.recordCheckOut(new Date().toISOString().split('T')[0])
      setTodayRecord(result.record)
      setSuccess('Salida registrada exitosamente')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al registrar salida')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (time) => {
    if (!time) return '--:--'
    return time.substring(0, 5)
  }

  const getLastBlock = () => {
    if (!todayRecord?.work_blocks || todayRecord.work_blocks.length === 0) return null
    return todayRecord.work_blocks[todayRecord.work_blocks.length - 1]
  }

  const isLastBlockOpen = () => {
    const lastBlock = getLastBlock()
    if (!lastBlock) return false
    return lastBlock.start_time === lastBlock.end_time
  }

  const formatTimeFromString = (timeStr) => {
    if (!timeStr) return '--:--'
    return timeStr.substring(0, 5)
  }

  const calculatePastDayHours = () => {
    const [inHour, inMin] = pastDayData.check_in.split(':').map(Number)
    const [outHour, outMin] = pastDayData.check_out.split(':').map(Number)
    
    let hours = outHour - inHour
    let minutes = outMin - inMin
    
    if (minutes < 0) {
      hours--
      minutes += 60
    }
    
    return `${hours}h ${minutes}m`
  }

  const handleRecordPastDayHours = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      await timeTrackingService.recordPastDayHours(
        pastDayData.date,
        pastDayData.check_in,
        pastDayData.check_out
      )
      setSuccess('Horas registradas exitosamente')
      setShowPastDayForm(false)
      setPastDayData({
        date: new Date().toISOString().split('T')[0],
        check_in: '09:00',
        check_out: '17:00'
      })
      loadTodayRecord()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al registrar horas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Carga de Horarios</h1>
        <div className="text-2xl font-mono text-gray-600">
          {currentTime.toLocaleTimeString('es-AR')}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
          {success}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Clock className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Bloques de Trabajo</h2>
        </div>

        <div className="space-y-4">
          {todayRecord?.work_blocks && todayRecord.work_blocks.length > 0 ? (
            <>
              {todayRecord.work_blocks.map((block, idx) => (
                <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600 mb-1">Bloque {idx + 1}</p>
                      <p className="text-lg font-mono font-bold text-gray-900">
                        {formatTimeFromString(block.start_time)} - {formatTimeFromString(block.end_time)}
                      </p>
                    </div>
                    {block.start_time !== block.end_time && (
                      <div className="text-right">
                        <p className="text-xs text-gray-500 mb-1">Duración</p>
                        <p className="text-lg font-semibold text-green-600">
                          {(() => {
                            const [sHour, sMin] = block.start_time.split(':').map(Number)
                            const [eHour, eMin] = block.end_time.split(':').map(Number)
                            let h = eHour - sHour
                            let m = eMin - sMin
                            if (m < 0) {
                              h--
                              m += 60
                            }
                            return `${h}h ${m}m`
                          })()}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </>
          ) : (
            <p className="text-gray-500 text-center py-4">Sin registros de hoy</p>
          )}
        </div>

        <div className="mt-6 grid grid-cols-2 gap-4">
          <button
            onClick={handleCheckIn}
            disabled={loading}
            className="py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <LogIn className="w-5 h-5" />
            {loading ? 'Registrando...' : 'Nueva Entrada'}
          </button>

          <button
            onClick={handleCheckOut}
            disabled={loading || !isLastBlockOpen()}
            className={`py-3 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors ${
              isLastBlockOpen()
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            <LogOut className="w-5 h-5" />
            {loading ? 'Registrando...' : 'Registrar Salida'}
          </button>
        </div>
      </div>

      {todayRecord?.total_hours > 0 || todayRecord?.total_minutes > 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Clock className="w-6 h-6 text-green-600" />
            <h2 className="text-xl font-semibold text-gray-900">Total del Día</h2>
          </div>

          <div className="bg-green-50 rounded-lg p-6 border border-green-200">
            <p className="text-center text-3xl font-mono font-bold text-green-600">
              {todayRecord.total_hours}h {todayRecord.total_minutes}m
            </p>
          </div>
        </div>
      ) : null}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Calendar className="w-6 h-6 text-purple-600" />
          <h2 className="text-xl font-semibold text-gray-900">Información</h2>
        </div>

        <div className="space-y-3 text-sm text-gray-600">
          <p>
            <strong>Fecha:</strong> {new Date().toLocaleDateString('es-AR', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </p>
          <p>
            <strong>Estado:</strong> {
              !todayRecord?.actual_check_in
                ? '⏳ Esperando entrada'
                : !todayRecord?.actual_check_out
                ? '✓ En turno'
                : '✓ Turno completado'
            }
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Calendar className="w-6 h-6 text-indigo-600" />
            <h2 className="text-xl font-semibold text-gray-900">Registrar Horas en Días Anteriores</h2>
          </div>
          <button
            onClick={() => setShowPastDayForm(!showPastDayForm)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
          >
            {showPastDayForm ? 'Cancelar' : 'Agregar Horas'}
          </button>
        </div>

        {showPastDayForm && (
          <div className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fecha
              </label>
              <input
                type="date"
                value={pastDayData.date}
                max={new Date().toISOString().split('T')[0]}
                onChange={(e) => setPastDayData({ ...pastDayData, date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hora de Entrada
                </label>
                <input
                  type="time"
                  value={pastDayData.check_in}
                  onChange={(e) => setPastDayData({ ...pastDayData, check_in: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hora de Salida
                </label>
                <input
                  type="time"
                  value={pastDayData.check_out}
                  onChange={(e) => setPastDayData({ ...pastDayData, check_out: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">
                <strong>Horas a registrar:</strong> {calculatePastDayHours()}
              </p>
            </div>

            <button
              onClick={handleRecordPastDayHours}
              disabled={loading}
              className="w-full py-3 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Registrando...' : 'Registrar Horas'}
            </button>
          </div>
        )}
      </div>

      <WorkHistoryView />
    </div>
  )
}

export default TimeTracking
