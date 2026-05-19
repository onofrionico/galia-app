import { useState, useEffect } from 'react'
import { CheckCircle, Info, X } from 'lucide-react'
import { useNotification } from '../../context/NotificationContext'

const NotificationToast = () => {
  const { notifications, removeNotification } = useNotification()
  const [visibleNotifications, setVisibleNotifications] = useState([])

  useEffect(() => {
    setVisibleNotifications(notifications)
  }, [notifications])

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5" />
      case 'info':
        return <Info className="w-5 h-5" />
      case 'error':
        return <X className="w-5 h-5" />
      default:
        return <CheckCircle className="w-5 h-5" />
    }
  }

  const getColors = (type) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800'
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800'
      default:
        return 'bg-green-50 border-green-200 text-green-800'
    }
  }

  const getIconColors = (type) => {
    switch (type) {
      case 'success':
        return 'text-green-500'
      case 'info':
        return 'text-blue-500'
      case 'error':
        return 'text-red-500'
      default:
        return 'text-green-500'
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm">
      {visibleNotifications.map((notification) => (
        <div
          key={notification.id}
          className={`flex items-start gap-3 p-4 rounded-lg border shadow-md animate-slideIn ${getColors(
            notification.type
          )}`}
          style={{
            animation: 'slideIn 0.3s ease-out',
          }}
        >
          <div className={`flex-shrink-0 mt-0.5 ${getIconColors(notification.type)}`}>
            {getIcon(notification.type)}
          </div>
          <div className="flex-1 pr-2">
            <p className="text-sm font-medium">{notification.message}</p>
          </div>
          <button
            onClick={() => removeNotification(notification.id)}
            className="flex-shrink-0 text-current opacity-50 hover:opacity-100 transition-opacity"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(100%);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </div>
  )
}

export default NotificationToast
