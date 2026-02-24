import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import employeeService from '../services/employeeService'
import { validateCUIL, validateAge, validateEmail, validatePhone, formatCUIL } from '../utils/validators'
import { User, Save, AlertCircle, CheckCircle } from 'lucide-react'

const Profile = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const [validationErrors, setValidationErrors] = useState({})
  const [employeeData, setEmployeeData] = useState(null)

  const [formData, setFormData] = useState({
    cuil: '',
    birth_date: '',
    email: '',
    phone: '',
    address: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: '',
    profile_photo_url: ''
  })

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      setLoading(true)
      const employee = await employeeService.getMyProfile()
      
      setEmployeeData(employee)
      setFormData({
        cuil: employee.cuil || '',
        birth_date: employee.birth_date || '',
        email: employee.email || '',
        phone: employee.phone || '',
        address: employee.address || '',
        emergency_contact_phone: employee.emergency_contact_phone || '',
        emergency_contact_relationship: employee.emergency_contact_relationship || '',
        profile_photo_url: employee.profile_photo_url || ''
      })
    } catch (err) {
      setError('Error al cargar perfil: ' + (err.response?.data?.error || err.message))
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
    
    if (success) setSuccess(false)
  }

  const validateForm = () => {
    const errors = {}

    if (formData.cuil && formData.cuil.trim()) {
      const cuilValidation = validateCUIL(formData.cuil)
      if (!cuilValidation.valid) errors.cuil = cuilValidation.error
    }

    if (formData.birth_date) {
      const ageValidation = validateAge(formData.birth_date)
      if (!ageValidation.valid) errors.birth_date = ageValidation.error
    }

    if (formData.email && formData.email.trim()) {
      const emailValidation = validateEmail(formData.email)
      if (!emailValidation.valid) errors.email = emailValidation.error
    }

    if (formData.phone && formData.phone.trim()) {
      const phoneValidation = validatePhone(formData.phone)
      if (!phoneValidation.valid) errors.phone = phoneValidation.error
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
      setSuccess(false)

      await employeeService.updateMyProfile(formData)
      
      setSuccess(true)
      setTimeout(() => setSuccess(false), 5000)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar perfil')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando perfil...</div>
      </div>
    )
  }

  if (!employeeData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">No se encontró información del empleado</div>
      </div>
    )
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-100 rounded-lg">
          <User className="text-blue-600" size={24} />
        </div>
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Mi Perfil</h1>
          <p className="text-sm text-gray-600">{employeeData.full_name}</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-3 md:p-4 flex items-start gap-3">
          <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={18} />
          <div className="text-xs md:text-sm text-red-700">{error}</div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border-l-4 border-green-500 p-3 md:p-4 flex items-start gap-3">
          <CheckCircle className="text-green-500 flex-shrink-0 mt-0.5" size={18} />
          <div className="text-xs md:text-sm text-green-700">Perfil actualizado exitosamente</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 md:space-y-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6 space-y-4 md:space-y-6">
          <div>
            <h2 className="text-lg md:text-xl font-semibold text-gray-900 mb-3 md:mb-4">Información Personal</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-6">
              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                  CUIL
                </label>
                <input
                  type="text"
                  name="cuil"
                  value={formData.cuil}
                  onChange={handleChange}
                  maxLength="13"
                  placeholder="XX-XXXXXXXX-X"
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm ${
                    validationErrors.cuil ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.cuil && (
                  <p className="text-red-500 text-xs md:text-sm mt-1">{validationErrors.cuil}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">Formato: XX-XXXXXXXX-X</p>
              </div>

              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                  Fecha de Nacimiento
                </label>
                <input
                  type="date"
                  name="birth_date"
                  value={formData.birth_date}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm ${
                    validationErrors.birth_date ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.birth_date && (
                  <p className="text-red-500 text-xs md:text-sm mt-1">{validationErrors.birth_date}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">Debe ser mayor de 18 años</p>
              </div>

              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="tu@email.com"
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm ${
                    validationErrors.email ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.email && (
                  <p className="text-red-500 text-xs md:text-sm mt-1">{validationErrors.email}</p>
                )}
              </div>

              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                  Teléfono
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="+54 9 11 1234-5678"
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 text-sm ${
                    validationErrors.phone ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {validationErrors.phone && (
                  <p className="text-red-500 text-xs md:text-sm mt-1">{validationErrors.phone}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">Mínimo 10 dígitos</p>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                  Dirección
                </label>
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  placeholder="Av. Corrientes 1234, CABA"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                  Foto de Perfil (URL)
                </label>
                <input
                  type="url"
                  name="profile_photo_url"
                  value={formData.profile_photo_url}
                  onChange={handleChange}
                  placeholder="https://ejemplo.com/foto.jpg"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 md:p-6 space-y-4 md:space-y-6">
          <div>
            <h2 className="text-lg md:text-xl font-semibold text-gray-900 mb-3 md:mb-4">Contacto de Emergencia</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-6">
              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                  Teléfono Emergencia
                </label>
                <input
                  type="tel"
                  name="emergency_contact_phone"
                  value={formData.emergency_contact_phone}
                  onChange={handleChange}
                  placeholder="+54 9 11 1234-5678"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                  Relación Contacto Emergencia
                </label>
                <input
                  type="text"
                  name="emergency_contact_relationship"
                  value={formData.emergency_contact_relationship}
                  onChange={handleChange}
                  placeholder="Ej: Madre, Hermano, Cónyuge"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border-l-4 border-blue-500 p-3 md:p-4">
          <p className="text-xs md:text-sm text-blue-700">
            <strong>Nota:</strong> Los campos marcados con <span className="text-red-500">*</span> son obligatorios. 
            Los cambios se guardarán inmediatamente al presionar "Guardar Cambios".
          </p>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save size={20} />
            {saving ? 'Guardando...' : 'Guardar Cambios'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default Profile
