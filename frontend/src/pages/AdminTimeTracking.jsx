import { useState, useEffect } from 'react'
import { timeTrackingService } from '../services/timeTrackingService'
import employeeService from '../services/employeeService'
import { Clock, Edit2, Trash2, Plus, Search, Calendar, AlertCircle, Check } from 'lucide-react'

const formatDateLocal = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const AdminTimeTracking = () => {
  const [records, setRecords] = useState([])
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  
  const [filters, setFilters] = useState({
    employee_id: '',
    start_date: '',
    end_date: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear()
  })

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createData, setCreateData] = useState({
    employee_id: '',
    date: formatDateLocal(new Date()),
    check_in: '09:00',
    check_out: '17:00'
  })

  const [editingBlock, setEditingBlock] = useState(null)
  const [editData, setEditData] = useState({
    start_time: '',
    end_time: ''
  })

  useEffect(() => {
    loadEmployees()
    loadRecords()
  }, [])

  const loadEmployees = async () => {
    try {
      const data = await employeeService.getEmployees()
      setEmployees(Array.isArray(data) ? data : (data?.employees || []))
    } catch (err) {
      console.error('Error loading employees:', err)
      setEmployees([])
    }
  }

  const loadRecords = async () => {
    setLoading(true)
    setError(null)
    try {
      const filterParams = {}
      if (filters.employee_id) filterParams.employee_id = filters.employee_id
      if (filters.month && filters.year) {
        filterParams.month = filters.month
        filterParams.year = filters.year
      } else {
        if (filters.start_date) filterParams.start_date = filters.start_date
        if (filters.end_date) filterParams.end_date = filters.end_date
      }

      const data = await timeTrackingService.adminGetAllRecords(filterParams)
      setRecords(data)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar registros')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateRecord = async () => {
    if (!createData.employee_id) {
      setError('Debe seleccionar un empleado')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      await timeTrackingService.adminCreateRecord(
        createData.employee_id,
        createData.date,
        createData.check_in,
        createData.check_out
      )
      setSuccess('Registro creado exitosamente')
      setShowCreateForm(false)
      setCreateData({
        employee_id: '',
        date: formatDateLocal(new Date()),
        check_in: '09:00',
        check_out: '17:00'
      })
      loadRecords()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear registro')
    } finally {
      setLoading(false)
    }
  }

  const handleEditBlock = (block) => {
    setEditingBlock(block.id)
    setEditData({
      start_time: block.start_time.substring(0, 5),
      end_time: block.end_time.substring(0, 5)
    })
  }

  const handleUpdateBlock = async (blockId) => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      await timeTrackingService.adminUpdateWorkBlock(
        blockId,
        editData.start_time,
        editData.end_time
      )
      setSuccess('Bloque actualizado exitosamente')
      setEditingBlock(null)
      loadRecords()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar bloque')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteBlock = async (blockId) => {
    if (!window.confirm('¿Está seguro de eliminar este bloque de trabajo?')) {
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      await timeTrackingService.adminDeleteWorkBlock(blockId)
      setSuccess('Bloque eliminado exitosamente')
      loadRecords()
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al eliminar bloque')
    } finally {
      setLoading(false)
    }
  }

  const calculateDuration = (startTime, endTime) => {
    const [sHour, sMin] = startTime.split(':').map(Number)
    const [eHour, eMin] = endTime.split(':').map(Number)
    let h = eHour - sHour
    let m = eMin - sMin
    if (m < 0) {
      h--
      m += 60
    }
    return `${h}h ${m}m`
  }

  const hasOngoingBlock = (record) => {
    return record.work_blocks && record.work_blocks.some(block => block.start_time === block.end_time)
  }

  const getEmployeeName = (employeeId) => {
    const employee = employees.find(e => e.id === employeeId)
    return employee ? employee.full_name : 'Desconocido'
  }

  const formatDate = (dateString) => {
    // Parse the date string as local date to avoid timezone issues
    const [year, month, day] = dateString.split('-').map(Number)
    const date = new Date(year, month - 1, day)
    return date.toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Gestión de Horas Trabajadas</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          {showCreateForm ? 'Cancelar' : 'Nuevo Registro'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <Check className="w-5 h-5" />
          {success}
        </div>
      )}

      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Crear Registro de Horas</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Empleado *
              </label>
              <select
                value={createData.employee_id}
                onChange={(e) => setCreateData({ ...createData, employee_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
              >
                <option value="">Seleccionar empleado</option>
                {employees.map(emp => (
                  <option key={emp.id} value={emp.id}>
                    {emp.full_name} - DNI: {emp.dni}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fecha *
              </label>
              <input
                type="date"
                value={createData.date}
                onChange={(e) => setCreateData({ ...createData, date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hora de Entrada *
              </label>
              <input
                type="time"
                value={createData.check_in}
                onChange={(e) => setCreateData({ ...createData, check_in: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hora de Salida *
              </label>
              <input
                type="time"
                value={createData.check_out}
                onChange={(e) => setCreateData({ ...createData, check_out: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
              />
            </div>
          </div>

          <div className="mt-4 flex justify-end gap-3">
            <button
              onClick={() => setShowCreateForm(false)}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleCreateRecord}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Creando...' : 'Crear Registro'}
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Search className="w-5 h-5 text-gray-600" />
          <h2 className="text-xl font-semibold text-gray-900">Filtros</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Empleado
            </label>
            <select
              value={filters.employee_id}
              onChange={(e) => setFilters({ ...filters, employee_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              <option value="">Todos los empleados</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>
                  {emp.full_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mes
            </label>
            <select
              value={filters.month}
              onChange={(e) => setFilters({ ...filters, month: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                <option key={m} value={m}>
                  {new Date(2000, m - 1).toLocaleString('es-AR', { month: 'long' })}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Año
            </label>
            <select
              value={filters.year}
              onChange={(e) => setFilters({ ...filters, year: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            >
              {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={loadRecords}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Buscando...' : 'Buscar'}
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Clock className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">
            Registros ({records.length})
          </h2>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Cargando registros...</div>
        ) : records.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No se encontraron registros</div>
        ) : (
          <div className="space-y-4">
            {records.map((record) => {
              const isOngoing = hasOngoingBlock(record)
              return (
                <div key={record.id} className={`border rounded-lg p-4 ${
                  isOngoing ? 'border-green-400 bg-green-50' : 'border-gray-200'
                }`}>
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lg text-gray-900">
                          {record.employee_name}
                        </h3>
                        {isOngoing && (
                          <span className="px-2 py-1 text-xs font-medium bg-green-600 text-white rounded-full flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            En turno
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">
                        DNI: {record.employee_dni} | Fecha: {formatDate(record.tracking_date)}
                      </p>
                    </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Total</p>
                    <p className="text-lg font-semibold text-green-600">
                      {record.total_hours}h {record.total_minutes}m
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  {record.work_blocks && record.work_blocks.map((block) => (
                    <div key={block.id} className="bg-gray-50 rounded-lg p-3 flex items-center justify-between">
                      {editingBlock === block.id ? (
                        <div className="flex items-center gap-3 flex-1">
                          <input
                            type="time"
                            value={editData.start_time}
                            onChange={(e) => setEditData({ ...editData, start_time: e.target.value })}
                            className="px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-600"
                          />
                          <span>-</span>
                          <input
                            type="time"
                            value={editData.end_time}
                            onChange={(e) => setEditData({ ...editData, end_time: e.target.value })}
                            className="px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-600"
                          />
                          <button
                            onClick={() => handleUpdateBlock(block.id)}
                            className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                          >
                            Guardar
                          </button>
                          <button
                            onClick={() => setEditingBlock(null)}
                            className="px-3 py-1 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 transition-colors"
                          >
                            Cancelar
                          </button>
                        </div>
                      ) : (
                        <>
                          <div className="flex-1">
                            {(() => {
                              const isOngoing = block.start_time === block.end_time
                              return (
                                <>
                                  <p className="font-mono font-semibold text-gray-900">
                                    {block.start_time.substring(0, 5)} - {isOngoing ? 'En curso' : block.end_time.substring(0, 5)}
                                  </p>
                                  {!isOngoing && (
                                    <p className="text-sm text-gray-600">
                                      Duración: {calculateDuration(block.start_time, block.end_time)}
                                    </p>
                                  )}
                                </>
                              )
                            })()}
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleEditBlock(block)}
                              className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                              title="Editar"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteBlock(block.id)}
                              className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                              title="Eliminar"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminTimeTracking
