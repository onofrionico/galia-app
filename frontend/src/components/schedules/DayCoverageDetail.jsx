import { useState } from 'react'
import { format, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'
import { X, Clock, User, Briefcase, UserPlus } from 'lucide-react'
import AddShiftModal from './AddShiftModal'

const DayCoverageDetail = ({ date, employees, onClose, onShiftAdded }) => {
  const [showAddShift, setShowAddShift] = useState(false)

  const handleShiftAdded = () => {
    setShowAddShift(false)
    if (onShiftAdded) {
      onShiftAdded()
    }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Cobertura del Día
              </h2>
              <p className="text-sm text-gray-600 capitalize">
                {format(parseISO(date), "EEEE, d 'de' MMMM 'de' yyyy", { locale: es })}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 overflow-auto p-4">
            {!employees || employees.length === 0 ? (
              <div className="text-center p-8">
                <User className="h-12 w-12 mx-auto text-gray-400 mb-3" />
                <p className="text-gray-500 mb-4">
                  No hay empleados asignados para este día
                </p>
                <button
                  onClick={() => setShowAddShift(true)}
                  className="inline-flex items-center px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  Asignar Empleado
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                    <User className="h-5 w-5 mr-2 text-primary" />
                    Empleados Asignados ({employees.length})
                  </h3>
                  <button
                    onClick={() => setShowAddShift(true)}
                    className="inline-flex items-center px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
                  >
                    <UserPlus className="h-4 w-4 mr-1.5" />
                    Asignar
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-3">
                  {employees.map((employee) => (
                    <div
                      key={employee.shift_id}
                      className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-primary transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center mb-2">
                            <User className="h-4 w-4 mr-2 text-gray-500" />
                            <span className="font-semibold text-gray-900">
                              {employee.employee_name}
                            </span>
                          </div>
                          
                          <div className="flex items-center mb-2 text-sm text-gray-600">
                            <Briefcase className="h-3.5 w-3.5 mr-2 text-gray-400" />
                            <span>{employee.job_position}</span>
                          </div>

                          <div className="flex items-center text-sm">
                            <Clock className="h-3.5 w-3.5 mr-2 text-gray-400" />
                            <span className="font-medium text-gray-700">
                              {employee.start_time} - {employee.end_time}
                            </span>
                            <span className="ml-2 text-gray-500">
                              ({employee.hours}h)
                            </span>
                          </div>
                        </div>

                        <div className="ml-4">
                          <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-primary text-white font-semibold text-sm">
                            {employee.employee_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-blue-900">
                        Total de Horas Programadas
                      </p>
                      <p className="text-xs text-blue-700 mt-1">
                        Suma de todas las horas asignadas para este día
                      </p>
                    </div>
                    <div className="text-2xl font-bold text-blue-900">
                      {employees.reduce((sum, emp) => sum + emp.hours, 0).toFixed(1)}h
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors font-medium"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>

      {showAddShift && (
        <AddShiftModal
          selectedDate={date}
          onClose={() => setShowAddShift(false)}
          onShiftAdded={handleShiftAdded}
        />
      )}
    </>
  )
}

export default DayCoverageDetail
