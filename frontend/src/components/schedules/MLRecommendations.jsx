import { useQuery } from '@tanstack/react-query'
import { Brain, TrendingUp, Users, DollarSign, AlertCircle, Sparkles } from 'lucide-react'
import api from '@/services/api'
import { format, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'

const MLRecommendations = ({ startDate, endDate }) => {
  const { data: recommendations, isLoading, error } = useQuery({
    queryKey: ['ml-recommendations', startDate, endDate],
    queryFn: async () => {
      const response = await api.get('/ml/recommendations/summary', {
        params: { start_date: startDate, end_date: endDate }
      })
      return response.data
    },
    enabled: !!startDate && !!endDate,
    retry: 1
  })

  if (isLoading) {
    return (
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <Brain className="h-6 w-6 text-purple-600 animate-pulse" />
          <div>
            <h3 className="font-semibold text-gray-900">Analizando datos...</h3>
            <p className="text-sm text-gray-600">Generando recomendaciones con IA</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !recommendations?.has_predictions) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-6 w-6 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 mb-2">
              Recomendaciones ML no disponibles
            </h3>
            <p className="text-sm text-gray-700 mb-3">
              {recommendations?.message || 'No hay suficientes datos históricos para generar predicciones.'}
            </p>
            <p className="text-xs text-gray-600">
              💡 <strong>Tip:</strong> El sistema necesita al menos 4 semanas de datos históricos 
              (turnos y ventas) para entrenar el modelo de predicción.
            </p>
          </div>
        </div>
      </div>
    )
  }

  const { daily_summary, model_version } = recommendations

  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="bg-purple-600 rounded-lg p-2">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 flex items-center space-x-2">
                <span>Recomendaciones con IA</span>
                <Sparkles className="h-4 w-4 text-purple-600" />
              </h3>
              <p className="text-sm text-gray-600">
                Predicciones basadas en datos históricos
              </p>
            </div>
          </div>
          {model_version && (
            <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded">
              v{model_version}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {daily_summary.map((day) => (
            <div
              key={day.date}
              className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="font-semibold text-gray-900">
                    {format(parseISO(day.date), 'EEEE', { locale: es })}
                  </div>
                  <div className="text-sm text-gray-500">
                    {format(parseISO(day.date), 'dd/MM/yyyy')}
                  </div>
                </div>
                <div className="bg-purple-100 rounded-full p-2">
                  <Users className="h-5 w-5 text-purple-600" />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 flex items-center space-x-1">
                    <TrendingUp className="h-4 w-4" />
                    <span>Ventas estimadas</span>
                  </span>
                  <span className="font-semibold text-gray-900">
                    {day.total_predicted_sales}
                  </span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 flex items-center space-x-1">
                    <DollarSign className="h-4 w-4" />
                    <span>Monto estimado</span>
                  </span>
                  <span className="font-semibold text-green-600">
                    ${day.total_predicted_amount.toLocaleString()}
                  </span>
                </div>

                <div className="pt-3 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Personal recomendado</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-lg font-bold text-purple-600">
                        {day.avg_staff_needed}
                      </span>
                      <span className="text-xs text-gray-500">promedio</span>
                    </div>
                  </div>
                  {day.peak_hour !== null && (
                    <div className="mt-2 text-xs text-gray-600 bg-gray-50 rounded px-2 py-1">
                      Pico: {day.peak_staff_needed} personas a las {day.peak_hour}:00
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 pt-4 border-t border-purple-200">
          <p className="text-xs text-gray-600 flex items-center space-x-1">
            <AlertCircle className="h-3 w-3" />
            <span>
              Las recomendaciones son estimaciones basadas en patrones históricos. 
              Ajusta según eventos especiales o condiciones particulares.
            </span>
          </p>
        </div>
      </div>
    </div>
  )
}

export default MLRecommendations
