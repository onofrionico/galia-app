import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import employeeService from '../services/employeeService'
import { ArrowLeft, Edit, UserX, Mail, Phone, MapPin, Calendar, Briefcase, AlertCircle, User, Clock } from 'lucide-react'

const EmployeeDetail = () => {
  const navigate = useNavigate()
  const { id } = useParams()
  const [employee, setEmployee] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showDeactivateModal, setShowDeactivateModal] = useState(false)

  useEffect(() => {
    loadEmployee()
  }, [id])

  const loadEmployee = async () => {
    try {
      setLoading(true)
      const data = await employeeService.getEmployee(id)
      setEmployee(data)
      setError(null)
    } catch (err) {
      setError('Error al cargar empleado: ' + (err.response?.data?.error || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleDeactivate = async () => {
    try {
      await employeeService.deactivateEmployee(id)
      setShowDeactivateModal(false)
      navigate('/employees')
    } catch (err) {
      setError('Error al desactivar empleado: ' + (err.response?.data?.error || err.message))
    }
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      activo: { bg: 'bg-green-100', text: 'text-green-800', label: 'Activo' },
      inactivo: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Inactivo' },
      suspendido: { bg: 'bg-red-100', text: 'text-red-800', label: 'Suspendido' },
      vacaciones: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Vacaciones' },
      licencia: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Licencia' }
    }
    const config = statusConfig[status] || statusConfig.activo
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    )
  }

  const getContractTypeBadge = (type) => {
    const typeConfig = {
      por_hora: { label: 'Por Hora', color: 'blue' },
      part_time: { label: 'Part Time', color: 'purple' },
      full_time: { label: 'Full Time', color: 'green' }
    }
    const config = typeConfig[type] || { label: type, color: 'gray' }
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium bg-${config.color}-100 text-${config.color}-800`}>
        {config.label}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4">
        <div className="text-red-700">{error}</div>
      </div>
    )
  }

  if (!employee) {
    return (
      <div className="text-center text-gray-500 py-8">
        Empleado no encontrado
      </div>
    )
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/employees')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0"
          >
            <ArrowLeft size={18} />
          </button>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Detalle del Empleado</h1>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => navigate(`/employees/${id}/edit`)}
            className="flex items-center justify-center gap-2 px-3 md:px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm md:text-base"
          >
            <Edit size={16} />
            <span className="hidden sm:inline">Editar</span>
          </button>
          {employee.status !== 'inactivo' && (
            <button
              onClick={() => setShowDeactivateModal(true)}
              className="flex items-center justify-center gap-2 px-3 md:px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm md:text-base"
            >
              <UserX size={16} />
              <span className="hidden sm:inline">Desactivar</span>
            </button>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-4 md:px-6 py-6 md:py-8">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 md:gap-6">
            <div className="flex-shrink-0">
              {employee.profile_photo_url ? (
                <img
                  src={employee.profile_photo_url}
                  alt={employee.full_name}
                  className="w-20 md:w-24 h-20 md:h-24 rounded-full border-4 border-white object-cover"
                />
              ) : (
                <div className="w-20 md:w-24 h-20 md:h-24 rounded-full border-4 border-white bg-white flex items-center justify-center flex-shrink-0">
                  <span className="text-blue-600 font-bold text-2xl md:text-3xl">
                    {employee.first_name?.[0]}{employee.last_name?.[0]}
                  </span>
                </div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h2 className="text-xl md:text-2xl font-bold text-white mb-2 truncate">{employee.full_name}</h2>
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-white/90 text-sm md:text-base">
                <div className="flex items-center gap-2">
                  <Briefcase size={16} />
                  <span className="truncate">{employee.job_position?.name || 'Sin puesto asignado'}</span>
                </div>
                <div>{getStatusBadge(employee.status)}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 md:p-6 space-y-4 md:space-y-6">
          <div>
            <h3 className="text-base md:text-lg font-semibold text-gray-900 mb-3 md:mb-4 flex items-center gap-2">
              <User size={18} className="text-gray-400" />
              Información Personal
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
              <div className="flex items-start gap-3">
                <Mail size={16} className="text-gray-400 mt-1 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs md:text-sm text-gray-500">Email</div>
                  <div className="text-sm md:text-base text-gray-900 truncate">{employee.email}</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Phone size={16} className="text-gray-400 mt-1 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs md:text-sm text-gray-500">Teléfono</div>
                  <div className="text-sm md:text-base text-gray-900">{employee.phone}</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <MapPin size={16} className="text-gray-400 mt-1 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs md:text-sm text-gray-500">Dirección</div>
                  <div className="text-sm md:text-base text-gray-900 truncate">{employee.address}</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Calendar size={16} className="text-gray-400 mt-1 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs md:text-sm text-gray-500">Nacimiento</div>
                  <div className="text-sm md:text-base text-gray-900">
                    {employee.birth_date ? new Date(employee.birth_date).toLocaleDateString('es-AR') : 'N/A'}
                    {employee.age && <span className="text-gray-500 ml-1">({employee.age}a)</span>}
                  </div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <User size={16} className="text-gray-400 mt-1 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs md:text-sm text-gray-500">DNI</div>
                  <div className="text-sm md:text-base text-gray-900">{employee.dni}</div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <User size={16} className="text-gray-400 mt-1 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs md:text-sm text-gray-500">CUIL</div>
                  <div className="text-sm md:text-base text-gray-900">{employee.cuil}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="border-t pt-4 md:pt-6">
            <h3 className="text-base md:text-lg font-semibold text-gray-900 mb-3 md:mb-4 flex items-center gap-2">
              <Briefcase size={18} className="text-gray-400" />
              Información Laboral
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
              <div>
                <div className="text-xs md:text-sm text-gray-500">Puesto Actual</div>
                <div className="text-sm md:text-base text-gray-900 font-medium truncate">{employee.job_position?.name || 'Sin asignar'}</div>
                {employee.job_position && (
                  <div className="mt-1">{getContractTypeBadge(employee.job_position.contract_type)}</div>
                )}
              </div>
              <div>
                <div className="text-xs md:text-sm text-gray-500">Relación Laboral</div>
                <div className="text-sm md:text-base text-gray-900 capitalize">{employee.employment_relationship}</div>
              </div>
              <div>
                <div className="text-xs md:text-sm text-gray-500">Fecha de Ingreso</div>
                <div className="text-sm md:text-base text-gray-900">
                  {employee.hire_date ? new Date(employee.hire_date).toLocaleDateString('es-AR') : 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-xs md:text-sm text-gray-500">Estado</div>
                <div className="mt-1">{getStatusBadge(employee.status)}</div>
              </div>
            </div>
          </div>

          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <AlertCircle size={20} className="text-gray-400" />
              Contacto de Emergencia
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">Nombre</div>
                <div className="text-gray-900">{employee.emergency_contact_name}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Teléfono</div>
                <div className="text-gray-900">{employee.emergency_contact_phone}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Relación</div>
                <div className="text-gray-900">{employee.emergency_contact_relationship}</div>
              </div>
            </div>
          </div>

          {employee.job_history && employee.job_history.length > 0 && (
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Clock size={20} className="text-gray-400" />
                Historial de Puestos
              </h3>
              <div className="space-y-3">
                {employee.job_history.map((history) => (
                  <div key={history.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{history.job_position?.name}</div>
                      <div className="text-sm text-gray-500">
                        {new Date(history.start_date).toLocaleDateString('es-AR')} - 
                        {history.end_date ? new Date(history.end_date).toLocaleDateString('es-AR') : 'Actual'}
                      </div>
                      {history.notes && (
                        <div className="text-sm text-gray-600 mt-1">{history.notes}</div>
                      )}
                    </div>
                    {history.is_current && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                        Actual
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {showDeactivateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Confirmar Desactivación</h3>
            <p className="text-gray-600 mb-6">
              ¿Estás seguro de que deseas desactivar a <strong>{employee.full_name}</strong>?
              Esta acción eliminará todos sus turnos futuros asignados y deshabilitará su acceso al sistema.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeactivateModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleDeactivate}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Desactivar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default EmployeeDetail
