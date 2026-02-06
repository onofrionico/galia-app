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

    const [inHour, inMin] = pastDayData.check_in.split(':').map(Number)
    const [outHour, outMin] = pastDayData.check_out.split(':').map(Number)
    const checkInTime = inHour * 60 + inMin
    const checkOutTime = outHour * 60 + outMin

    if (todayRecord?.work_blocks && todayRecord.work_blocks.length > 0) {
      for (const block of todayRecord.work_blocks) {
        const [bsHour, bsMin] = block.start_time.split(':').map(Number)
        const [beHour, beMin] = block.end_time.split(':').map(Number)
        const blockStart = bsHour * 60 + bsMin
        const blockEnd = beHour * 60 + beMin

        if (checkInTime < blockEnd && blockStart < checkOutTime) {
          setError('Este bloque se superpone con otro bloque existente')
          setLoading(false)
          return
        }
      }
    }

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
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-2">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Carga de Horarios</h1>
        <div className="text-xl md:text-2xl font-mono text-gray-600 bg-gray-100 px-3 py-2 rounded-lg w-fit">
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

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6">
        <div className="flex items-center gap-3 mb-4 md:mb-6">
          <Clock className="w-5 md:w-6 h-5 md:h-6 text-blue-600" />
          <h2 className="text-lg md:text-xl font-semibold text-gray-900">Bloques de Trabajo</h2>
        </div>

        <div className="space-y-3 md:space-y-4 mb-4 md:mb-6">
          {todayRecord?.work_blocks && todayRecord.work_blocks.length > 0 ? (
            <>
              {todayRecord.work_blocks.map((block, idx) => (
                <div key={idx} className="bg-gray-50 rounded-lg p-3 md:p-4 border border-gray-200">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div>
                      <p className="text-xs md:text-sm text-gray-600 mb-1">Bloque {idx + 1}</p>
                      <p className="text-base md:text-lg font-mono font-bold text-gray-900">
                        {formatTimeFromString(block.start_time)} - {formatTimeFromString(block.end_time)}
                      </p>
                    </div>
                    {block.start_time !== block.end_time && (
                      <div className="text-left sm:text-right">
                        <p className="text-xs text-gray-500 mb-1">Duración</p>
                        <p className="text-base md:text-lg font-semibold text-green-600">
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

        <div className="grid grid-cols-2 gap-3 md:gap-4">
          <button
            onClick={handleCheckIn}
            disabled={loading}
            className="py-3 px-3 md:px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold flex items-center justify-center gap-2 text-sm md:text-base disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <LogIn className="w-4 md:w-5 h-4 md:h-5" />
            <span className="hidden sm:inline">{loading ? 'Registrando...' : 'Nueva Entrada'}</span>
            <span className="sm:hidden">{loading ? '...' : 'Entrada'}</span>
          </button>

          <button
            onClick={handleCheckOut}
            disabled={loading || !isLastBlockOpen()}
            className={`py-3 px-3 md:px-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors text-sm md:text-base ${
              isLastBlockOpen()
                ? 'bg-red-600 text-white hover:bg-red-700'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            <LogOut className="w-4 md:w-5 h-4 md:h-5" />
            <span className="hidden sm:inline">{loading ? 'Registrando...' : 'Registrar Salida'}</span>
            <span className="sm:hidden">{loading ? '...' : 'Salida'}</span>
          </button>
        </div>
      </div>

      {todayRecord?.total_hours > 0 || todayRecord?.total_minutes > 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6">
          <div className="flex items-center gap-3 mb-4">
            <Clock className="w-5 md:w-6 h-5 md:h-6 text-green-600" />
            <h2 className="text-lg md:text-xl font-semibold text-gray-900">Total del Día</h2>
          </div>

          <div className="bg-green-50 rounded-lg p-4 md:p-6 border border-green-200">
            <p className="text-center text-2xl md:text-3xl font-mono font-bold text-green-600">
              {todayRecord.total_hours}h {todayRecord.total_minutes}m
            </p>
          </div>
        </div>
      ) : null}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6">
        <div className="flex items-center gap-3 mb-4">
          <Calendar className="w-5 md:w-6 h-5 md:h-6 text-purple-600" />
          <h2 className="text-lg md:text-xl font-semibold text-gray-900">Información</h2>
        </div>

        <div className="space-y-2 md:space-y-3 text-xs md:text-sm text-gray-600">
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

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 md:mb-6">
          <div className="flex items-center gap-3">
            <Calendar className="w-5 md:w-6 h-5 md:h-6 text-indigo-600" />
            <h2 className="text-lg md:text-xl font-semibold text-gray-900">Registrar Horas Anteriores</h2>
          </div>
          <button
            onClick={() => setShowPastDayForm(!showPastDayForm)}
            className="px-3 md:px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-xs md:text-sm font-medium w-full sm:w-auto"
          >
            {showPastDayForm ? 'Cancelar' : 'Agregar Horas'}
          </button>
        </div>

        {showPastDayForm && (
          <div className="space-y-3 md:space-y-4 p-3 md:p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">
                Fecha
              </label>
              <input
                type="date"
                value={pastDayData.date}
                max={new Date().toISOString().split('T')[0]}
                onChange={(e) => setPastDayData({ ...pastDayData, date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600 text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-3 md:gap-4">
              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">
                  Entrada
                </label>
                <input
                  type="time"
                  value={pastDayData.check_in}
                  onChange={(e) => setPastDayData({ ...pastDayData, check_in: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-2">
                  Salida
                </label>
                <input
                  type="time"
                  value={pastDayData.check_out}
                  onChange={(e) => setPastDayData({ ...pastDayData, check_out: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-600 text-sm"
                />
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs md:text-sm text-blue-800">
                <strong>Horas a registrar:</strong> {calculatePastDayHours()}
              </p>
            </div>

            <button
              onClick={handleRecordPastDayHours}
              disabled={loading}
              className="w-full py-3 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-semibold text-sm md:text-base disabled:opacity-50 disabled:cursor-not-allowed"
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
