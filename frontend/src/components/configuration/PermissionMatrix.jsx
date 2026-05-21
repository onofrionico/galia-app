import { useState } from 'react'

export const PermissionMatrix = ({ permissions, onPermissionsChange, isLoading, mode = 'role' }) => {
  const [sortBy, setSortBy] = useState('name')

  const handleToggle = (moduleId) => {
    const updated = permissions.map(perm => {
      if (perm.module_id === moduleId) {
        return { ...perm, is_granted: !perm.is_granted }
      }
      return perm
    })
    onPermissionsChange(updated)
  }

  const handleToggleAll = () => {
    const allGranted = permissions.every(p => p.is_granted)
    const updated = permissions.map(perm => ({
      ...perm,
      is_granted: !allGranted
    }))
    onPermissionsChange(updated)
  }

  const sortedPermissions = [...permissions].sort((a, b) => {
    if (sortBy === 'name') {
      return a.module_name.localeCompare(b.module_name)
    } else if (sortBy === 'category') {
      return (a.display_name || '').localeCompare(b.display_name || '')
    }
    return 0
  })

  const allGranted = permissions.every(p => p.is_granted)
  const grantedCount = permissions.filter(p => p.is_granted).length

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Matriz de Permisos</h3>
            <p className="mt-1 text-sm text-gray-500">
              {grantedCount} de {permissions.length} módulos habilitados
            </p>
          </div>
          <div className="flex gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm bg-white hover:border-gray-400"
            >
              <option value="name">Ordenar por nombre</option>
              <option value="category">Ordenar por categoría</option>
            </select>
            <button
              onClick={handleToggleAll}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md disabled:opacity-50"
            >
              {allGranted ? 'Deshabilitarlo Todo' : 'Habilitarlo Todo'}
            </button>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <input
                  type="checkbox"
                  checked={allGranted}
                  onChange={handleToggleAll}
                  disabled={isLoading}
                  className="h-4 w-4 cursor-pointer"
                />
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Módulo
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Descripción
              </th>
              {mode === 'user' && (
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rol
                </th>
              )}
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Acceso
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedPermissions.map((perm) => (
              <tr key={perm.module_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    checked={perm.is_granted || false}
                    onChange={() => handleToggle(perm.module_id)}
                    disabled={isLoading}
                    className="h-4 w-4 cursor-pointer rounded border-gray-300"
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{perm.icon || '📦'}</span>
                    <div>
                      <div className="text-sm font-medium text-gray-900">{perm.module_name}</div>
                      <div className="text-xs text-gray-500">{perm.display_name}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <p className="text-sm text-gray-600">{perm.description || '-'}</p>
                </td>
                {mode === 'user' && (
                  <td className="px-6 py-4 whitespace-nowrap">
                    {perm.is_override ? (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        ⚠️ Personalizado
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        📋 Rol
                      </span>
                    )}
                  </td>
                )}
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                    perm.is_granted
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {perm.is_granted ? '✓ Habilitado' : '✗ Deshabilitado'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
