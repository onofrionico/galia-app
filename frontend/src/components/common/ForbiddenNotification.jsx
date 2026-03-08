import { useEffect, useState } from 'react'
import { XCircle, AlertTriangle } from 'lucide-react'

/**
 * Componente para mostrar notificaciones de acceso denegado (403)
 * Escucha el evento 'forbidden-access' disparado por el interceptor de API
 */
export default function ForbiddenNotification() {
  const [notification, setNotification] = useState(null)

  useEffect(() => {
    const handleForbiddenAccess = (event) => {
      const { message, path } = event.detail
      
      setNotification({
        message,
        path,
        timestamp: new Date()
      })

      // Auto-ocultar después de 5 segundos
      setTimeout(() => {
        setNotification(null)
      }, 5000)
    }

    // Escuchar evento de acceso denegado
    window.addEventListener('forbidden-access', handleForbiddenAccess)

    return () => {
      window.removeEventListener('forbidden-access', handleForbiddenAccess)
    }
  }, [])

  if (!notification) return null

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in">
      <div className="bg-red-50 border-l-4 border-red-500 rounded-lg shadow-lg p-4 max-w-md">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <AlertTriangle className="h-6 w-6 text-red-500" />
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium text-red-800">
              Acceso Denegado
            </h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{notification.message}</p>
              {notification.path && (
                <p className="mt-1 text-xs text-red-600">
                  Recurso: {notification.path}
                </p>
              )}
            </div>
            <div className="mt-3 text-xs text-red-600">
              Serás redirigido al inicio en unos segundos...
            </div>
          </div>
          <div className="ml-4 flex-shrink-0">
            <button
              onClick={() => setNotification(null)}
              className="inline-flex text-red-400 hover:text-red-600 focus:outline-none"
            >
              <XCircle className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
