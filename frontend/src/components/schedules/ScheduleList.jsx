import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { scheduleService } from '@/services/scheduleService'
import { Calendar, Plus, Eye, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

const ScheduleList = ({ onSelectSchedule, onCreateNew }) => {
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const queryClient = useQueryClient()
  
  const { data: schedules, isLoading, error } = useQuery({
    queryKey: ['schedules'],
    queryFn: scheduleService.getSchedules,
  })
  
  const deleteMutation = useMutation({
    mutationFn: scheduleService.deleteSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries(['schedules'])
      setDeleteConfirm(null)
    },
    onError: (error) => {
      alert(error.response?.data?.error || 'Error al eliminar la grilla')
    }
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-500">Cargando grillas...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error al cargar las grillas: {error.message}</p>
      </div>
    )
  }

  const getStatusBadge = (status) => {
    const styles = {
      draft: 'bg-yellow-100 text-yellow-800',
      published: 'bg-green-100 text-green-800',
    }
    const labels = {
      draft: 'Borrador',
      published: 'Publicada',
    }
    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${styles[status]}`}>
        {labels[status]}
      </span>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Grillas Horarias</h2>
        <button
          onClick={onCreateNew}
          className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>Nueva Grilla</span>
        </button>
      </div>

      {schedules && schedules.length === 0 ? (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">No hay grillas horarias creadas</p>
          <button
            onClick={onCreateNew}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            Crear primera grilla
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {schedules?.map((schedule) => (
            <div
              key={schedule.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <Calendar className="h-5 w-5 text-gray-400" />
                    <h3 className="text-lg font-medium text-gray-900">
                      {format(new Date(schedule.start_date), 'dd MMM', { locale: es })} - {format(new Date(schedule.end_date), 'dd MMM yyyy', { locale: es })}
                    </h3>
                    {getStatusBadge(schedule.status)}
                  </div>
                  <p className="text-sm text-gray-500">
                    Creada el {format(new Date(schedule.created_at), 'dd/MM/yyyy HH:mm', { locale: es })}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onSelectSchedule(schedule)}
                    className="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors"
                    title="Ver detalles"
                  >
                    <Eye className="h-5 w-5" />
                  </button>
                  {schedule.status === 'draft' && (
                    <button
                      onClick={() => setDeleteConfirm(schedule)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Eliminar grilla"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Confirmar eliminación
            </h3>
            <p className="text-gray-600 mb-4">
              ¿Estás seguro de que deseas eliminar la grilla del{' '}
              {format(new Date(deleteConfirm.start_date), 'dd MMM', { locale: es })} al{' '}
              {format(new Date(deleteConfirm.end_date), 'dd MMM yyyy', { locale: es })}?
            </p>
            <p className="text-sm text-gray-500 mb-6">
              Esta acción no se puede deshacer.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                disabled={deleteMutation.isPending}
              >
                Cancelar
              </button>
              <button
                onClick={() => deleteMutation.mutate(deleteConfirm.id)}
                className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50"
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? 'Eliminando...' : 'Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ScheduleList
