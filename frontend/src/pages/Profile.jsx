import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { User, Lock, Mail, Phone, MapPin, AlertCircle, Save, X, Edit2, UserCircle, Shield } from 'lucide-react'
import api from '@/services/api'

const Profile = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  
  const [profile, setProfile] = useState(null)
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    address: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: ''
  })
  
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/profile')
      setProfile(response.data)
      
      if (response.data.employee) {
        setFormData({
          email: response.data.user.email || '',
          first_name: response.data.employee.first_name || '',
          last_name: response.data.employee.last_name || '',
          phone: response.data.employee.phone || '',
          address: response.data.employee.address || '',
          emergency_contact_name: response.data.employee.emergency_contact_name || '',
          emergency_contact_phone: response.data.employee.emergency_contact_phone || '',
          emergency_contact_relationship: response.data.employee.emergency_contact_relationship || ''
        })
      } else {
        setFormData({
          ...formData,
          email: response.data.user.email || ''
        })
      }
    } catch (err) {
      console.error('Error al cargar perfil:', err)
      setError('Error al cargar el perfil')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handlePasswordChange = (e) => {
    const { name, value } = e.target
    setPasswordData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    try {
      setSaving(true)
      setError(null)
      setSuccess(null)
      
      const response = await api.put('/profile', formData)
      setProfile(response.data.profile)
      setSuccess('Perfil actualizado exitosamente')
      setIsEditing(false)
      
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      console.error('Error al actualizar perfil:', err)
      setError(err.response?.data?.error || 'Error al actualizar el perfil')
    } finally {
      setSaving(false)
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('Las contraseñas no coinciden')
      return
    }
    
    if (passwordData.new_password.length < 6) {
      setError('La nueva contraseña debe tener al menos 6 caracteres')
      return
    }
    
    try {
      setSaving(true)
      setError(null)
      setSuccess(null)
      
      await api.put('/profile/password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      })
      
      setSuccess('Contraseña actualizada exitosamente')
      setIsChangingPassword(false)
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      })
      
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      console.error('Error al cambiar contraseña:', err)
      setError(err.response?.data?.error || 'Error al cambiar la contraseña')
    } finally {
      setSaving(false)
    }
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setError(null)
    if (profile?.employee) {
      setFormData({
        email: profile.user.email || '',
        first_name: profile.employee.first_name || '',
        last_name: profile.employee.last_name || '',
        phone: profile.employee.phone || '',
        address: profile.employee.address || '',
        emergency_contact_name: profile.employee.emergency_contact_name || '',
        emergency_contact_phone: profile.employee.emergency_contact_phone || '',
        emergency_contact_relationship: profile.employee.emergency_contact_relationship || ''
      })
    }
  }

  const handleCancelPasswordChange = () => {
    setIsChangingPassword(false)
    setError(null)
    setPasswordData({
      current_password: '',
      new_password: '',
      confirm_password: ''
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Cargando perfil...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Mi Perfil</h1>
          <p className="text-muted-foreground mt-1">Gestiona tu información personal y configuración de cuenta</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg flex items-start space-x-2">
          <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg flex items-start space-x-2">
          <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
          <span>{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <UserCircle className="h-6 w-6 text-primary" />
                <h2 className="text-xl font-semibold">Información Personal</h2>
              </div>
              {!isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-primary hover:bg-primary/10 rounded-lg transition-colors"
                >
                  <Edit2 className="h-4 w-4" />
                  <span>Editar</span>
                </button>
              )}
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre
                  </label>
                  <input
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleInputChange}
                    disabled={!isEditing || !profile?.employee}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Apellido
                  </label>
                  <input
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleInputChange}
                    disabled={!isEditing || !profile?.employee}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Mail className="h-4 w-4 inline mr-1" />
                  Email
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
              </div>

              {profile?.employee && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <Phone className="h-4 w-4 inline mr-1" />
                      Teléfono
                    </label>
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      <MapPin className="h-4 w-4 inline mr-1" />
                      Dirección
                    </label>
                    <textarea
                      name="address"
                      value={formData.address}
                      onChange={handleInputChange}
                      disabled={!isEditing}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                    />
                  </div>

                  <div className="border-t pt-4 mt-4">
                    <h3 className="text-lg font-semibold mb-4">Contacto de Emergencia</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Nombre
                        </label>
                        <input
                          type="text"
                          name="emergency_contact_name"
                          value={formData.emergency_contact_name}
                          onChange={handleInputChange}
                          disabled={!isEditing}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                        />
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Teléfono
                          </label>
                          <input
                            type="tel"
                            name="emergency_contact_phone"
                            value={formData.emergency_contact_phone}
                            onChange={handleInputChange}
                            disabled={!isEditing}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Relación
                          </label>
                          <input
                            type="text"
                            name="emergency_contact_relationship"
                            value={formData.emergency_contact_relationship}
                            onChange={handleInputChange}
                            disabled={!isEditing}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {isEditing && (
                <div className="flex space-x-3 pt-4">
                  <button
                    type="submit"
                    disabled={saving}
                    className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Save className="h-4 w-4" />
                    <span>{saving ? 'Guardando...' : 'Guardar Cambios'}</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    disabled={saving}
                    className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <X className="h-4 w-4" />
                    <span>Cancelar</span>
                  </button>
                </div>
              )}
            </form>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <Lock className="h-6 w-6 text-primary" />
                <h2 className="text-xl font-semibold">Seguridad</h2>
              </div>
              {!isChangingPassword && (
                <button
                  onClick={() => setIsChangingPassword(true)}
                  className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-primary hover:bg-primary/10 rounded-lg transition-colors"
                >
                  <Edit2 className="h-4 w-4" />
                  <span>Cambiar Contraseña</span>
                </button>
              )}
            </div>

            {!isChangingPassword ? (
              <div className="text-sm text-muted-foreground">
                <p>Tu contraseña está protegida y encriptada.</p>
                <p className="mt-2">Última actualización: {new Date(profile?.user?.created_at).toLocaleDateString('es-AR')}</p>
              </div>
            ) : (
              <form onSubmit={handleChangePassword} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contraseña Actual
                  </label>
                  <input
                    type="password"
                    name="current_password"
                    value={passwordData.current_password}
                    onChange={handlePasswordChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nueva Contraseña
                  </label>
                  <input
                    type="password"
                    name="new_password"
                    value={passwordData.new_password}
                    onChange={handlePasswordChange}
                    required
                    minLength={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                  <p className="text-xs text-muted-foreground mt-1">Mínimo 6 caracteres</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Confirmar Nueva Contraseña
                  </label>
                  <input
                    type="password"
                    name="confirm_password"
                    value={passwordData.confirm_password}
                    onChange={handlePasswordChange}
                    required
                    minLength={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>

                <div className="flex space-x-3 pt-4">
                  <button
                    type="submit"
                    disabled={saving}
                    className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Save className="h-4 w-4" />
                    <span>{saving ? 'Guardando...' : 'Cambiar Contraseña'}</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelPasswordChange}
                    disabled={saving}
                    className="flex items-center space-x-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <X className="h-4 w-4" />
                    <span>Cancelar</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center space-x-3 mb-4">
              <User className="h-6 w-6 text-primary" />
              <h2 className="text-xl font-semibold">Información de Cuenta</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Email</p>
                <p className="font-medium">{profile?.user?.email}</p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Rol</p>
                <div className="flex items-center space-x-2 mt-1">
                  <Shield className="h-4 w-4 text-primary" />
                  <span className="font-medium capitalize">{profile?.user?.role === 'admin' ? 'Administrador' : 'Empleado'}</span>
                </div>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Estado</p>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${
                  profile?.user?.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {profile?.user?.is_active ? 'Activo' : 'Inactivo'}
                </span>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Miembro desde</p>
                <p className="font-medium">{new Date(profile?.user?.created_at).toLocaleDateString('es-AR', { 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}</p>
              </div>
            </div>
          </div>

          {profile?.employee && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-4">Información Laboral</h2>
              
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">DNI</p>
                  <p className="font-medium">{profile.employee.dni}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">CUIL</p>
                  <p className="font-medium">{profile.employee.cuil}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Fecha de Nacimiento</p>
                  <p className="font-medium">{new Date(profile.employee.birth_date).toLocaleDateString('es-AR')}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Edad</p>
                  <p className="font-medium">{profile.employee.age} años</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Fecha de Ingreso</p>
                  <p className="font-medium">{new Date(profile.employee.hire_date).toLocaleDateString('es-AR')}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Relación Laboral</p>
                  <p className="font-medium capitalize">{profile.employee.employment_relationship}</p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">Estado</p>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${
                    profile.employee.status === 'activo' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {profile.employee.status}
                  </span>
                </div>

                {profile.employee.job_position && (
                  <div>
                    <p className="text-sm text-muted-foreground">Puesto</p>
                    <p className="font-medium">{profile.employee.job_position.name}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Profile
