import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'
import { PermissionMatrix } from '@/components/configuration/PermissionMatrix'
import { API_BASE_URL, getAuthHeader, getJsonHeader } from '@/config/api'

const ROLES = ['admin', 'employee', 'supervisor']

export default function Permissions() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('roles')
  const [selectedRole, setSelectedRole] = useState('admin')
  const [selectedUser, setSelectedUser] = useState(null)
  const [users, setUsers] = useState([])
  const [rolePermissions, setRolePermissions] = useState([])
  const [userPermissions, setUserPermissions] = useState([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    if (!user || user.role !== 'admin') return
    fetchUsers()
  }, [user])

  useEffect(() => {
    if (activeTab === 'roles' && selectedRole) {
      fetchRolePermissions(selectedRole)
    }
  }, [selectedRole, activeTab])

  useEffect(() => {
    if (activeTab === 'users' && selectedUser) {
      fetchUserPermissions(selectedUser.id)
    }
  }, [selectedUser, activeTab])

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/employees?limit=1000`, {
        headers: getAuthHeader()
      })
      if (response.ok) {
        const data = await response.json()
        setUsers(data.employees || [])
      }
    } catch (error) {
      console.error('Error fetching users:', error)
    }
  }

  const fetchRolePermissions = async (role) => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/permissions/role/${role}`, {
        headers: getAuthHeader()
      })
      if (response.ok) {
        const data = await response.json()
        console.log('[Permissions] Role permissions loaded:', data)
        setRolePermissions(data.permissions || [])
      } else {
        console.error('[Permissions] Error response:', response.status)
        setMessage({ type: 'error', text: `Error al cargar permisos: ${response.status}` })
      }
    } catch (error) {
      console.error('Error fetching role permissions:', error)
      setMessage({ type: 'error', text: 'Error al cargar los permisos del rol' })
    } finally {
      setLoading(false)
    }
  }

  const fetchUserPermissions = async (userId) => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/permissions/user/${userId}`, {
        headers: getAuthHeader()
      })
      if (response.ok) {
        const data = await response.json()
        console.log('[Permissions] User permissions loaded:', data)
        setUserPermissions(data.permissions || [])
      } else {
        console.error('[Permissions] Error response:', response.status)
        setMessage({ type: 'error', text: `Error al cargar permisos: ${response.status}` })
      }
    } catch (error) {
      console.error('Error fetching user permissions:', error)
      setMessage({ type: 'error', text: 'Error al cargar los permisos del usuario' })
    } finally {
      setLoading(false)
    }
  }

  const handleSaveRolePermissions = async () => {
    setSaving(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/permissions/role/${selectedRole}`, {
        method: 'PUT',
        headers: getJsonHeader(),
        body: JSON.stringify({
          permissions: rolePermissions.map(p => ({
            module_id: p.module_id,
            is_granted: p.is_granted
          }))
        })
      })
      if (response.ok) {
        setMessage({ type: 'success', text: 'Permisos del rol actualizados exitosamente' })
        setTimeout(() => setMessage(null), 3000)
      } else {
        setMessage({ type: 'error', text: 'Error al actualizar los permisos' })
      }
    } catch (error) {
      console.error('Error saving permissions:', error)
      setMessage({ type: 'error', text: 'Error al guardar los permisos' })
    } finally {
      setSaving(false)
    }
  }

  const handleSaveUserPermissions = async () => {
    if (!selectedUser) return
    setSaving(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/permissions/user/${selectedUser.id}`, {
        method: 'PUT',
        headers: getJsonHeader(),
        body: JSON.stringify({
          permissions: userPermissions.map(p => ({
            module_id: p.module_id,
            is_granted: p.is_granted
          }))
        })
      })
      if (response.ok) {
        setMessage({ type: 'success', text: 'Permisos del usuario actualizados exitosamente' })
        setTimeout(() => setMessage(null), 3000)
      } else {
        setMessage({ type: 'error', text: 'Error al actualizar los permisos' })
      }
    } catch (error) {
      console.error('Error saving user permissions:', error)
      setMessage({ type: 'error', text: 'Error al guardar los permisos' })
    } finally {
      setSaving(false)
    }
  }

  const handleResetUserPermissions = async () => {
    if (!selectedUser || !window.confirm('¿Estás seguro? Esto eliminará todos los permisos personalizados del usuario.')) {
      return
    }
    setSaving(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/permissions/user/${selectedUser.id}/reset`, {
        method: 'POST',
        headers: getAuthHeader()
      })
      if (response.ok) {
        setMessage({ type: 'success', text: 'Permisos del usuario reseteados a los valores por defecto del rol' })
        setTimeout(() => setMessage(null), 3000)
        fetchUserPermissions(selectedUser.id)
      } else {
        setMessage({ type: 'error', text: 'Error al resetear los permisos' })
      }
    } catch (error) {
      console.error('Error resetting permissions:', error)
      setMessage({ type: 'error', text: 'Error al resetear los permisos' })
    } finally {
      setSaving(false)
    }
  }

  if (!user || user.role !== 'admin') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900">Acceso Denegado</h2>
          <p className="mt-2 text-gray-600">Solo los administradores pueden acceder a esta página.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Administrador de Permisos</h1>
          <p className="mt-2 text-gray-600">Configura los permisos de módulos para roles y usuarios</p>
        </div>

        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {message.text}
          </div>
        )}

        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <div className="flex">
              <button
                onClick={() => setActiveTab('roles')}
                className={`px-6 py-4 font-medium text-sm ${
                  activeTab === 'roles'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Permisos por Rol
              </button>
              <button
                onClick={() => setActiveTab('users')}
                className={`px-6 py-4 font-medium text-sm ${
                  activeTab === 'users'
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Permisos por Usuario
              </button>
            </div>
          </div>

          <div className="p-6">
            {activeTab === 'roles' ? (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Seleccionar Rol
                  </label>
                  <select
                    value={selectedRole}
                    onChange={(e) => setSelectedRole(e.target.value)}
                    className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {ROLES.map(role => (
                      <option key={role} value={role}>
                        {role.charAt(0).toUpperCase() + role.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {loading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  </div>
                ) : (
                  <>
                    <PermissionMatrix
                      permissions={rolePermissions}
                      onPermissionsChange={setRolePermissions}
                      isLoading={saving}
                      mode="role"
                    />
                    <div className="flex justify-end">
                      <button
                        onClick={handleSaveRolePermissions}
                        disabled={saving || loading}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      >
                        {saving ? 'Guardando...' : 'Guardar Cambios'}
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Seleccionar Usuario
                  </label>
                  <select
                    value={selectedUser?.id || ''}
                    onChange={(e) => {
                      const user = users.find(u => u.id === parseInt(e.target.value))
                      setSelectedUser(user)
                    }}
                    className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Seleccionar un usuario...</option>
                    {users.map(user => (
                      <option key={user.id} value={user.id}>
                        {user.name || `${user.first_name} ${user.last_name}`}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedUser && (
                  <>
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <p className="text-sm text-blue-800">
                        <strong>Rol del usuario:</strong> {selectedUser.role || 'No asignado'}
                      </p>
                    </div>

                    {loading ? (
                      <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      </div>
                    ) : (
                      <>
                        <PermissionMatrix
                          permissions={userPermissions}
                          onPermissionsChange={setUserPermissions}
                          isLoading={saving}
                          mode="user"
                        />
                        <div className="flex justify-between">
                          <button
                            onClick={handleResetUserPermissions}
                            disabled={saving || loading}
                            className="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 disabled:opacity-50"
                          >
                            Resetear a Rol
                          </button>
                          <button
                            onClick={handleSaveUserPermissions}
                            disabled={saving || loading}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                          >
                            {saving ? 'Guardando...' : 'Guardar Cambios'}
                          </button>
                        </div>
                      </>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
