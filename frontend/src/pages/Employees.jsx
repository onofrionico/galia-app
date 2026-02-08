import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import employeeService from '../services/employeeService'
import { jobPositionService } from '../services/jobPositionService'
import { Search, UserPlus, Filter, X, Mail, Phone, Briefcase, Calendar } from 'lucide-react'

const Employees = () => {
  const navigate = useNavigate()
  const [employees, setEmployees] = useState([])
  const [jobPositions, setJobPositions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showFilters, setShowFilters] = useState(false)
  
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    job_position_id: '',
    hire_date_from: '',
    hire_date_to: '',
    page: 1,
    limit: 10
  })
  
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    pages: 1,
    limit: 10
  })

  useEffect(() => {
    loadEmployees()
    loadJobPositions()
  }, [filters])

  const loadEmployees = async () => {
    try {
      setLoading(true)
      const data = await employeeService.getEmployees(filters)
      setEmployees(data.employees || [])
      setPagination({
        total: data.total || 0,
        page: data.page || 1,
        pages: data.pages || 1,
        limit: data.limit || 10
      })
      setError(null)
    } catch (err) {
      setError('Error al cargar empleados: ' + (err.response?.data?.error || err.message))
    } finally {
      setLoading(false)
    }
  }

  const loadJobPositions = async () => {
    try {
      const positions = await jobPositionService.getJobPositions({ is_active: 'true' })
      setJobPositions(positions || [])
    } catch (err) {
      console.error('Error al cargar puestos:', err)
    }
  }

  const handleSearchChange = (e) => {
    setFilters({ ...filters, search: e.target.value, page: 1 })
  }

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value, page: 1 })
  }

  const clearFilters = () => {
    setFilters({
      search: '',
      status: '',
      job_position_id: '',
      hire_date_from: '',
      hire_date_to: '',
      page: 1,
      limit: 10
    })
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
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    )
  }

  const handlePageChange = (newPage) => {
    setFilters({ ...filters, page: newPage })
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Gestión de Empleados</h1>
        <button
          onClick={() => navigate('/employees/new')}
          className="flex items-center justify-center gap-2 bg-blue-600 text-white px-3 md:px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm md:text-base w-full sm:w-auto"
        >
          <UserPlus size={18} />
          Nuevo Empleado
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-3 md:p-4 border-b border-gray-200">
          <div className="flex flex-col gap-3 md:flex-row md:gap-4 md:items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Buscar por nombre, DNI..."
                value={filters.search}
                onChange={handleSearchChange}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center justify-center gap-2 px-3 md:px-4 py-2 border rounded-lg transition-colors text-sm md:text-base ${
                showFilters ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Filter size={18} />
              <span className="hidden sm:inline">Filtros</span>
            </button>
          </div>

          {showFilters && (
            <div className="mt-3 md:mt-4 p-3 md:p-4 bg-gray-50 rounded-lg space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                <div>
                  <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">Estado</label>
                  <select
                    value={filters.status}
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  >
                    <option value="">Todos</option>
                    <option value="activo">Activo</option>
                    <option value="inactivo">Inactivo</option>
                    <option value="suspendido">Suspendido</option>
                    <option value="vacaciones">Vacaciones</option>
                    <option value="licencia">Licencia</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">Puesto</label>
                  <select
                    value={filters.job_position_id}
                    onChange={(e) => handleFilterChange('job_position_id', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  >
                    <option value="">Todos</option>
                    {jobPositions.map(pos => (
                      <option key={pos.id} value={pos.id}>{pos.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">Desde</label>
                  <input
                    type="date"
                    value={filters.hire_date_from}
                    onChange={(e) => handleFilterChange('hire_date_from', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">Hasta</label>
                  <input
                    type="date"
                    value={filters.hire_date_to}
                    onChange={(e) => handleFilterChange('hire_date_to', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={clearFilters}
                  className="flex items-center gap-2 px-3 md:px-4 py-2 text-xs md:text-sm text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  <X size={16} />
                  Limpiar filtros
                </button>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="p-4 bg-red-50 border-l-4 border-red-500 text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="p-6 md:p-8 text-center text-gray-500 text-sm md:text-base">
            Cargando empleados...
          </div>
        ) : employees.length === 0 ? (
          <div className="p-6 md:p-8 text-center text-gray-500 text-sm md:text-base">
            No se encontraron empleados
          </div>
        ) : (
          <>
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Empleado
                    </th>
                    <th className="px-4 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contacto
                    </th>
                    <th className="px-4 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Puesto
                    </th>
                    <th className="px-4 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Estado
                    </th>
                    <th className="px-4 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ingreso
                    </th>
                    <th className="px-4 md:px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {employees.map((employee) => (
                    <tr key={employee.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/employees/${employee.id}`)}>
                      <td className="px-4 md:px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            {employee.profile_photo_url ? (
                              <img className="h-10 w-10 rounded-full object-cover" src={employee.profile_photo_url} alt="" />
                            ) : (
                              <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                                <span className="text-blue-600 font-medium text-sm">
                                  {employee.first_name?.[0]}{employee.last_name?.[0]}
                                </span>
                              </div>
                            )}
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">{employee.full_name}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 md:px-6 py-4">
                        <div className="space-y-1">
                          <div className="flex items-center text-sm text-gray-600">
                            <Mail size={14} className="mr-2" />
                            {employee.email}
                          </div>
                          <div className="flex items-center text-sm text-gray-600">
                            <Phone size={14} className="mr-2" />
                            {employee.phone}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 md:px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-900">
                          <Briefcase size={14} className="mr-2 text-gray-400" />
                          {employee.job_position?.name || 'Sin asignar'}
                        </div>
                      </td>
                      <td className="px-4 md:px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(employee.status)}
                      </td>
                      <td className="px-4 md:px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center text-sm text-gray-600">
                          <Calendar size={14} className="mr-2 text-gray-400" />
                          {new Date(employee.hire_date).toLocaleDateString('es-AR')}
                        </div>
                      </td>
                      <td className="px-4 md:px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/employees/${employee.id}`)
                          }}
                          className="text-blue-600 hover:text-blue-900 mr-4"
                        >
                          Ver
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/employees/${employee.id}/edit`)
                          }}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          Editar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="md:hidden space-y-3 p-3 md:p-4">
              {employees.map((employee) => (
                <div
                  key={employee.id}
                  onClick={() => navigate(`/employees/${employee.id}`)}
                  className="bg-white border border-gray-200 rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start gap-3 mb-3">
                    <div className="flex-shrink-0 h-12 w-12">
                      {employee.profile_photo_url ? (
                        <img className="h-12 w-12 rounded-full object-cover" src={employee.profile_photo_url} alt="" />
                      ) : (
                        <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                          <span className="text-blue-600 font-medium text-sm">
                            {employee.first_name?.[0]}{employee.last_name?.[0]}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-gray-900 truncate">{employee.full_name}</h3>
                      <p className="text-xs text-gray-500 truncate">{employee.job_position?.name || 'Sin asignar'}</p>
                    </div>
                    <div>
                      {getStatusBadge(employee.status)}
                    </div>
                  </div>

                  <div className="space-y-2 text-xs text-gray-600 mb-3">
                    <div className="flex items-center gap-2">
                      <Mail size={14} className="text-gray-400 flex-shrink-0" />
                      <span className="truncate">{employee.email}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Phone size={14} className="text-gray-400 flex-shrink-0" />
                      <span>{employee.phone}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar size={14} className="text-gray-400 flex-shrink-0" />
                      <span>{new Date(employee.hire_date).toLocaleDateString('es-AR')}</span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/employees/${employee.id}`)
                      }}
                      className="flex-1 px-3 py-2 text-xs font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100 transition-colors"
                    >
                      Ver
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/employees/${employee.id}/edit`)
                      }}
                      className="flex-1 px-3 py-2 text-xs font-medium text-indigo-600 bg-indigo-50 rounded hover:bg-indigo-100 transition-colors"
                    >
                      Editar
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {pagination.pages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Mostrando {((pagination.page - 1) * pagination.limit) + 1} a {Math.min(pagination.page * pagination.limit, pagination.total)} de {pagination.total} empleados
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handlePageChange(pagination.page - 1)}
                    disabled={pagination.page === 1}
                    className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => handlePageChange(pagination.page + 1)}
                    disabled={pagination.page === pagination.pages}
                    className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default Employees
