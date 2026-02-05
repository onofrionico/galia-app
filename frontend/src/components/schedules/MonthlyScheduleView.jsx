import { Clock } from 'lucide-react'

const MonthlyScheduleView = ({ schedule }) => {
  const getDaysInMonth = () => {
    const year = schedule.year
    const month = schedule.month
    return new Date(year, month, 0).getDate()
  }

  const getFirstDayOfMonth = () => {
    const year = schedule.year
    const month = schedule.month
    const firstDay = new Date(year, month - 1, 1).getDay()
    return firstDay === 0 ? 6 : firstDay - 1
  }

  const getShiftsForDate = (day) => {
    const year = schedule.year
    const month = schedule.month
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    return schedule.shifts_by_date[dateStr] || []
  }

  const isToday = (day) => {
    const today = new Date()
    const year = schedule.year
    const month = schedule.month
    
    return (
      today.getDate() === day &&
      today.getMonth() + 1 === month &&
      today.getFullYear() === year
    )
  }

  const daysInMonth = getDaysInMonth()
  const firstDayOffset = getFirstDayOfMonth()
  const totalCells = Math.ceil((daysInMonth + firstDayOffset) / 7) * 7

  const daysOfWeek = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
        <div>
          <p className="text-sm text-gray-600">Total de horas mensuales</p>
          <p className="text-2xl font-bold text-blue-600">{schedule.total_hours.toFixed(2)}h</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Turnos asignados</p>
          <p className="text-2xl font-bold text-gray-900">{schedule.shift_count}</p>
        </div>
      </div>

      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="grid grid-cols-7 bg-gray-50 border-b border-gray-200">
          {daysOfWeek.map((day) => (
            <div
              key={day}
              className="p-2 text-center text-sm font-semibold text-gray-700 border-r border-gray-200 last:border-r-0"
            >
              {day}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7">
          {Array.from({ length: totalCells }, (_, index) => {
            const dayNumber = index - firstDayOffset + 1
            const isValidDay = dayNumber > 0 && dayNumber <= daysInMonth
            const shifts = isValidDay ? getShiftsForDate(dayNumber) : []
            const today = isValidDay && isToday(dayNumber)

            return (
              <div
                key={index}
                className={`min-h-[100px] p-2 border-r border-b border-gray-200 ${
                  !isValidDay ? 'bg-gray-50' : today ? 'bg-blue-50' : 'bg-white'
                }`}
              >
                {isValidDay && (
                  <>
                    <div className="flex justify-between items-start mb-1">
                      <span
                        className={`text-sm font-medium ${
                          today ? 'text-blue-700' : 'text-gray-700'
                        }`}
                      >
                        {dayNumber}
                      </span>
                      {today && (
                        <span className="px-1.5 py-0.5 text-xs font-medium bg-blue-600 text-white rounded">
                          Hoy
                        </span>
                      )}
                    </div>

                    {shifts.length > 0 && (
                      <div className="space-y-1">
                        {shifts.map((shift, idx) => (
                          <div
                            key={idx}
                            className="text-xs p-1.5 bg-blue-100 text-blue-800 rounded border border-blue-200"
                          >
                            <div className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              <span className="font-medium">
                                {shift.start_time} - {shift.end_time}
                              </span>
                            </div>
                            <div className="text-blue-600 mt-0.5">
                              {shift.hours}h
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default MonthlyScheduleView
