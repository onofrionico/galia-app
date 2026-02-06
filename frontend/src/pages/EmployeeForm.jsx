import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { employeeService } from '../services/employeeService'
import { jobPositionService } from '../services/jobPositionService'
import { validateDNI, validateCUIL, validateAge, validateEmail, validatePhone, formatCUIL } from '../utils/validators'
import { ArrowLeft, Save, Upload, AlertCircle } from 'lucide-react'

const EmployeeForm = () => {
  const navigate = useNavigate()
  const { id } = useParams()
  const isEditMode = !!id

  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [jobPositions, setJobPositions] = useState([])
  const [validationErrors, setValidationErrors] = useState({})

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    dni: '',
    cuil: '',
    birth_date: '',
    phone: '',
    address: '',
    email: '',
    employment_relationship: 'dependencia',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: '',
    hire_date: new Date().toISOString().split('T')[0],
    job_position_id: '',
    password: '',
    profile_photo_url: ''
  })

  useEffect(() => {
    loadJobPositions()
    if (isEditMode) {
      loadEmployee()
    }
  }, [id])

  const loadJobPositions = async () => {
    try {
      const positions = await jobPositionService.getJobPositions({ is_active: 'true' })
      setJobPositions(positions || [])
    } catch (err) {
      console.error('Error al cargar puestos:', err)
    }
  }

  const loadEmployee = async () => {
    try {
      setLoading(true)
      const employee = await employeeService.getEmployee(id)
      setFormData({
        first_name: employee.first_name || '',
        last_name: employee.last_name || '',
        dni: employee.dni || '',
        cuil: employee.cuil || '',
        birth_date: employee.birth_date || '',
        phone: employee.phone || '',
        address: employee.address || '',
        email: employee.email || '',
        employment_relationship: employee.employment_relationship || 'dependencia',
        emergency_contact_name: employee.emergency_contact_name || '',
        emergency_contact_phone: employee.emergency_contact_phone || '',
        emergency_contact_relationship: employee.emergency_contact_relationship || '',
        hire_date: employee.hire_date || '',
        job_position_id: employee.job_position?.id || '',
        profile_photo_url: employee.profile_photo_url || '',
        password: ''
      })
    } catch (err) {
      setError('Error al cargar empleado: ' + (err.response?.data?.error || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    
    if (name === 'cuil') {
      setFormData({ ...formData, [name]: formatCUIL(value) })
    } else {
      setFormData({ ...formData, [name]: value })
    }
    
    if (validationErrors[name]) {
      setValidationErrors({ ...validationErrors, [name]: null })
    }
  }

  const validateForm = () => {
    const errors = {}

    if (!formData.first_name.trim()) errors.first_name = 'Nombre es requerido'
    if (!formData.last_name.trim()) errors.last_name = 'Apellido es requerido'

    const dniValidation = validateDNI(formData.dni)
    if (!dniValidation.valid) errors.dni = dniValidation.error

    const cuilValidation = validateCUIL(formData.cuil)
    if (!cuilValidation.valid) errors.cuil = cuilValidation.error

    const ageValidation = validateAge(formData.birth_date)
    if (!ageValidation.valid) errors.birth_date = ageValidation.error

    const emailValidation = validateEmail(formData.email)
    if (!emailValidation.valid) errors.email = emailValidation.error

    const phoneValidation = validatePhone(formData.phone)
    if (!phoneValidation.valid) errors.phone = phoneValidation.error

    if (!formData.address.trim()) errors.address = 'Dirección es requerida'
    if (!formData.emergency_contact_name.trim()) errors.emergency_contact_name = 'Nombre de contacto de emergencia es requerido'
    if (!formData.emergency_contact_phone.trim()) errors.emergency_contact_phone = 'Teléfono de emergencia es requerido'
    if (!formData.emergency_contact_relationship.trim()) errors.emergency_contact_relationship = 'Relación es requerida'
    if (!formData.hire_date) errors.hire_date = 'Fecha de ingreso es requerida'
    if (!formData.job_position_id) errors.job_position_id = 'Puesto es requerido'
    
    if (!isEditMode && !formData.password) {
      errors.password = 'Contraseña es requerida'
    } else if (!isEditMode && formData.password.length < 6) {
      errors.password = 'Contraseña debe tener al menos 6 caracteres'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      setError('Por favor corrige los errores en el formulario')
      return
    }

    try {
      setSaving(true)
      setError(null)

      if (isEditMode) {
        await employeeService.updateEmployee(id, formData)
      } else {
        await employeeService.createEmployee(formData)
      }

      navigate('/employees')
    } catch (err) {
      setError(err.response?.data?.error || 'Error al guardar empleado')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/employees')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0"
        >
          <ArrowLeft size={18} />
        </button>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
          {isEditMode ? 'Editar Empleado' : 'Nuevo Empleado'}
        </h1>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-3 md:p-4 flex items-start gap-3">
          <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={18} />
          <div className="text-xs md:text-sm text-red-700">{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 md:space-y-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6 space-y-4 md:space-y-6">
          <div>
            <h2 className="text-lg md:text-xl font-semibold text-gray-900 mb-3 md:mb-4">Información Personal</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-6">
              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                  Nombre <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm ${
                    validationErrors.first_name ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.first_name && (
                  <p className="text-red-500 text-xs md:text-sm mt-1">{validationErrors.first_name}</p>
                )}
              </div>

              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                  Apellido <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm ${
                    validationErrors.last_name ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.last_name && (
                  <p className="text-red-500 text-xs md:text-sm mt-1">{validationErrors.last_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  DNI <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="dni"
                  value={formData.dni}
                  onChange={handleChange}
                  maxLength="8"
                  placeholder="12345678"
                  disabled={isEditMode}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.dni ? 'border-red-500' : 'border-gray-300'
                  } ${isEditMode ? 'bg-gray-100' : ''}`}
                />
                {validationErrors.dni && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.dni}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CUIL <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="cuil"
                  value={formData.cuil}
                  onChange={handleChange}
                  maxLength="13"
                  placeholder="20-12345678-9"
                  disabled={isEditMode}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.cuil ? 'border-red-500' : 'border-gray-300'
                  } ${isEditMode ? 'bg-gray-100' : ''}`}
                />
                {validationErrors.cuil && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.cuil}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha de Nacimiento <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  name="birth_date"
                  value={formData.birth_date}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.birth_date ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.birth_date && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.birth_date}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="empleado@example.com"
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.email ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.email && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.email}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Teléfono <span className="text-red-500">*</span>
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="+54 9 11 1234-5678"
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.phone ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.phone && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.phone}</p>
                )}
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dirección <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  placeholder="Av. Corrientes 1234, CABA"
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.address ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.address && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.address}</p>
                )}
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Foto de Perfil (URL)
                </label>
                <div className="flex gap-2">
                  <input
                    type="url"
                    name="profile_photo_url"
                    value={formData.profile_photo_url}
                    onChange={handleChange}
                    placeholder="https://ejemplo.com/foto.jpg"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
                  >
                    <Upload size={16} />
                    Subir
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Información Laboral</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Relación Laboral <span className="text-red-500">*</span>
                </label>
                <select
                  name="employment_relationship"
                  value={formData.employment_relationship}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="dependencia">Relación de Dependencia</option>
                  <option value="monotributo">Monotributo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Puesto <span className="text-red-500">*</span>
                </label>
                <select
                  name="job_position_id"
                  value={formData.job_position_id}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.job_position_id ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">Seleccionar puesto...</option>
                  {jobPositions.map(pos => (
                    <option key={pos.id} value={pos.id}>
                      {pos.name} ({pos.contract_type})
                    </option>
                  ))}
                </select>
                {validationErrors.job_position_id && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.job_position_id}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha de Ingreso <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  name="hire_date"
                  value={formData.hire_date}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.hire_date ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.hire_date && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.hire_date}</p>
                )}
              </div>

              {!isEditMode && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contraseña Temporal <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Mínimo 6 caracteres"
                    className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                      validationErrors.password ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {validationErrors.password && (
                    <p className="text-red-500 text-sm mt-1">{validationErrors.password}</p>
                  )}
                  <p className="text-sm text-gray-500 mt-1">
                    El empleado deberá cambiarla en su primer acceso
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Contacto de Emergencia</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre Completo <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="emergency_contact_name"
                  value={formData.emergency_contact_name}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.emergency_contact_name ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.emergency_contact_name && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.emergency_contact_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Teléfono <span className="text-red-500">*</span>
                </label>
                <input
                  type="tel"
                  name="emergency_contact_phone"
                  value={formData.emergency_contact_phone}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.emergency_contact_phone ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.emergency_contact_phone && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.emergency_contact_phone}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Relación <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="emergency_contact_relationship"
                  value={formData.emergency_contact_relationship}
                  onChange={handleChange}
                  placeholder="Ej: Madre, Hermano, Cónyuge"
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    validationErrors.emergency_contact_relationship ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.emergency_contact_relationship && (
                  <p className="text-red-500 text-sm mt-1">{validationErrors.emergency_contact_relationship}</p>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/employees')}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save size={20} />
            {saving ? 'Guardando...' : 'Guardar Empleado'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default EmployeeForm
