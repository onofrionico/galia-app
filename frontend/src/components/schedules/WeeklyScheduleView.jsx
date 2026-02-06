import { Clock } from 'lucide-react'

const WeeklyScheduleView = ({ schedule }) => {
  const daysOfWeek = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
  
  const parseDate = (dateStr) => {
    const [year, month, day] = dateStr.split('-').map(Number)
    return new Date(year, month - 1, day)
  }
  
  const getShiftsForDay = (dayIndex) => {
    const startDate = parseDate(schedule.start_date)
    const targetDate = new Date(startDate)
    targetDate.setDate(targetDate.getDate() + dayIndex)
    const targetDateStr = targetDate.getFullYear() + '-' + 
                          String(targetDate.getMonth() + 1).padStart(2, '0') + '-' + 
                          String(targetDate.getDate()).padStart(2, '0')
    
    return schedule.shifts.filter(shift => shift.shift_date === targetDateStr)
  }

  const formatDate = (dayIndex) => {
    const startDate = parseDate(schedule.start_date)
    const targetDate = new Date(startDate)
    targetDate.setDate(targetDate.getDate() + dayIndex)
    return targetDate.toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })
  }

  const isToday = (dayIndex) => {
    const startDate = parseDate(schedule.start_date)
    const targetDate = new Date(startDate)
    targetDate.setDate(targetDate.getDate() + dayIndex)
    const today = new Date()
    
    return targetDate.getFullYear() === today.getFullYear() &&
           targetDate.getMonth() === today.getMonth() &&
           targetDate.getDate() === today.getDate()
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
        <div>
          <p className="text-sm text-gray-600">Total de horas semanales</p>
          <p className="text-2xl font-bold text-blue-600">{schedule.total_hours.toFixed(2)}h</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Turnos asignados</p>
          <p className="text-2xl font-bold text-gray-900">{schedule.shift_count}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {daysOfWeek.map((day, index) => {
          const shifts = getShiftsForDay(index)
          const dayIsToday = isToday(index)
          
          return (
            <div
              key={index}
              className={`border rounded-lg p-4 ${
                dayIsToday ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'
              }`}
            >
              <div className="flex justify-between items-center mb-2">
                <div>
                  <h3 className={`font-semibold ${dayIsToday ? 'text-blue-700' : 'text-gray-900'}`}>
                    {day}
                  </h3>
                  <p className="text-sm text-gray-500">{formatDate(index)}</p>
                </div>
                {dayIsToday && (
                  <span className="px-2 py-1 text-xs font-medium bg-blue-600 text-white rounded">
                    Hoy
                  </span>
                )}
              </div>

              {shifts.length === 0 ? (
                <p className="text-sm text-gray-400 italic">Sin turnos asignados</p>
              ) : (
                <div className="space-y-2">
                  {shifts.map((shift) => (
                    <div
                      key={shift.id}
                      className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                    >
                      <Clock className="w-4 h-4 text-gray-400" />
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">
                          {shift.start_time} - {shift.end_time}
                        </p>
                        <p className="text-sm text-gray-500">
                          {shift.hours} horas
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default WeeklyScheduleView
