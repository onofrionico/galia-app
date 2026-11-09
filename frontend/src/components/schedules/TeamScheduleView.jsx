import { Users } from 'lucide-react'

const DAY_NAMES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

const todayStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// Grilla completa de la semana (solo grillas publicadas y marcadas como visibles para el equipo)
const TeamScheduleView = ({ schedule }) => {
  if (!schedule.employees.length) {
    return (
      <div className="py-12 text-center text-gray-500">
        <Users className="mx-auto mb-3 h-10 w-10 text-gray-300" />
        <p>No hay una grilla del equipo para esta semana.</p>
        <p className="mt-1 text-sm">Aparece cuando se publica y se habilita para que la vean todos.</p>
      </div>
    )
  }

  const today = todayStr()

  return (
    <div className="-mx-4 overflow-x-auto md:mx-0">
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <thead>
          <tr>
            <th className="sticky left-0 z-10 bg-white px-3 py-2 text-left font-semibold text-gray-700">Empleado</th>
            {schedule.days.map((day, i) => (
              <th
                key={day}
                className={`px-2 py-2 text-center font-semibold ${day === today ? 'text-blue-700' : 'text-gray-700'}`}
              >
                <div>{DAY_NAMES[i]}</div>
                <div className="text-xs font-normal text-gray-500">{Number(day.slice(8, 10))}/{Number(day.slice(5, 7))}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {schedule.employees.map((row) => (
            <tr key={row.employee_id} className={`border-t border-gray-100 ${row.is_me ? 'bg-blue-50' : ''}`}>
              <td className={`sticky left-0 z-10 px-3 py-2 font-medium text-gray-900 ${row.is_me ? 'bg-blue-50' : 'bg-white'}`}>
                <div className="whitespace-nowrap">{row.employee_name}{row.is_me && <span className="ml-1 text-xs text-blue-700">(vos)</span>}</div>
                <div className="text-xs font-normal text-gray-500">{row.total_hours.toFixed(1)} h</div>
              </td>
              {schedule.days.map((day) => {
                const shifts = row.shifts.filter((s) => s.shift_date === day)
                return (
                  <td key={day} className={`px-1 py-2 text-center align-top ${day === today ? 'bg-blue-50/60' : ''}`}>
                    {shifts.length === 0 ? (
                      <span className="text-gray-300">—</span>
                    ) : (
                      <div className="flex flex-col gap-1">
                        {shifts.map((s) => (
                          <span key={s.id} className="whitespace-nowrap rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-800">
                            {s.start_time}–{s.end_time}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default TeamScheduleView
