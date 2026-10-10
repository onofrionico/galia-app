import { useState, useEffect } from 'react'
import { PermissionMatrix } from '@/components/configuration/PermissionMatrix'
import permissionsService from '@/services/permissionsService'
import employeeService from '@/services/employeeService'

// El admin siempre tiene acceso total; solo se configura el rol employee.
const ROLES = ['employee']
const ROLE_LABELS = { employee: 'Empleado', admin: 'Administrador' }

export default function Permissions() {
  const [activeTab, setActiveTab] = useState('roles')
  const [selectedRole, setSelectedRole] = useState('employee')
  const [selectedUser, setSelectedUser] = useState(null)
  const [users, setUsers] = useState([])
  const [rolePermissions, setRolePermissions] = useState([])
  const [userPermissions, setUserPermissions] = useState([])
  const [selectedUserRole, setSelectedUserRole] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    fetchUsers()
  }, [])

  useEffect(() => {
    if (activeTab === 'roles' && selectedRole) {
      fetchRolePermissions(selectedRole)
    }
  }, [selectedRole, activeTab])

  useEffect(() => {
    setUserPermissions([])
    setSelectedUserRole(null)
    if (activeTab === 'users' && selectedUser) {
      let ignore = false
      fetchUserPermissions(selectedUser.id, () => ignore)
      return () => {
        ignore = true
      }
    }
  }, [selectedUser, activeTab])

  const fetchUsers = async () => {
    try {
      const data = await employeeService.getEmployees({ limit: 1000 })
      // Los permisos son por usuario: usar user_id, no el id del empleado.
      setUsers(
        (data.employees || [])
          .filter(e => e.user_id)
          .map(e => ({ id: e.user_id, name: e.full_name || e.email, email: e.email }))
      )
    } catch (error) {
      setMessage({ type: 'error', text: 'Error al cargar los usuarios' })
    }
  }

  const fetchRolePermissions = async (role) => {
    setLoading(true)
    try {
      setRolePermissions(await permissionsService.getRolePermissions(role))
    } catch (error) {
      setMessage({ type: 'error', text: 'Error al cargar los permisos del rol' })
    } finally {
      setLoading(false)
    }
  }

  const fetchUserPermissions = async (userId, isStale = () => false) => {
    setLoading(true)
    try {
      const data = await permissionsService.getUserPermissions(userId)
      if (isStale()) return
      setUserPermissions(data.permissions)
      setSelectedUserRole(data.role)
    } catch (error) {
      if (isStale()) return
      setMessage({ type: 'error', text: 'Error al cargar los permisos del usuario' })
    } finally {
      if (!isStale()) setLoading(false)
    }
  }

  const toPayload = (permissions) => permissions.map(p => ({ module_id: p.module_id, is_granted: p.is_granted }))

  const flashSuccess = (text) => {
    setMessage({ type: 'success', text })
    setTimeout(() => setMessage(null), 3000)
  }

  const handleSaveRolePermissions = async () => {
    setSaving(true)
    try {
      await permissionsService.updateRolePermissions(selectedRole, toPayload(rolePermissions))
      flashSuccess('Permisos del rol actualizados')
    } catch (error) {
      setMessage({ type: 'error', text: 'Error al guardar los permisos' })
    } finally {
      setSaving(false)
    }
  }

  const handleSaveUserPermissions = async () => {
    if (!selectedUser) return
    setSaving(true)
    try {
      // Filas que coinciden con el rol se envían como null (heredan); sólo las
      // que difieren del rol se guardan como override explícito.
      const payload = userPermissions.map(p => ({
        module_id: p.module_id,
        is_granted: p.is_granted === p.role_permission ? null : p.is_granted,
      }))
      await permissionsService.updateUserPermissions(selectedUser.id, payload)
      flashSuccess('Permisos del usuario actualizados')
    } catch (error) {
      setMessage({ type: 'error', text: 'Error al guardar los permisos' })
    } finally {
      setSaving(false)
    }
  }

  const handleResetUserPermissions = async () => {
    if (!selectedUser || !window.confirm('¿Seguro? Se eliminan los permisos personalizados del usuario.')) return
    setSaving(true)
    try {
      await permissionsService.resetUserPermissions(selectedUser.id)
      flashSuccess('Permisos del usuario reseteados a los del rol')
      fetchUserPermissions(selectedUser.id)
    } catch (error) {
      setMessage({ type: 'error', text: 'Error al resetear los permisos' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8">
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
                        {ROLE_LABELS[role] || role}
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
                      const selected = users.find(u => u.id === parseInt(e.target.value))
                      setSelectedUser(selected || null)
                    }}
                    className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Seleccionar un usuario...</option>
                    {users.map(u => (
                      <option key={u.id} value={u.id}>
                        {u.name}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedUser && (
                  <>
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <p className="text-sm text-blue-800">
                        <strong>Rol del usuario:</strong> {ROLE_LABELS[selectedUserRole] || selectedUserRole || 'No asignado'}
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
