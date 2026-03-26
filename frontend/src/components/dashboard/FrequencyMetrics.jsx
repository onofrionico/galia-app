import React from 'react';
import { Calendar, TrendingUp, Activity, AlertTriangle } from 'lucide-react';

const FrequencyMetrics = ({ metrics, currentGap }) => {
  const getRegularityColor = (score) => {
    if (score >= 75) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRegularityLabel = (score) => {
    if (score >= 75) return 'Alta';
    if (score >= 50) return 'Media';
    return 'Baja';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Purchases */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Total de Compras</p>
            <p className="text-2xl font-bold text-gray-900">{metrics.total_purchases}</p>
            <p className="text-xs text-gray-500 mt-1">
              {metrics.purchases_per_month.toFixed(1)} por mes
            </p>
          </div>
          <Calendar className="w-8 h-8 text-blue-600" />
        </div>
      </div>

      {/* Average Days Between */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Días Promedio</p>
            <p className="text-2xl font-bold text-gray-900">
              {metrics.avg_days_between.toFixed(0)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              entre compras
            </p>
          </div>
          <TrendingUp className="w-8 h-8 text-purple-600" />
        </div>
      </div>

      {/* Regularity Score */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Regularidad</p>
            <p className={`text-2xl font-bold ${getRegularityColor(metrics.regularity_score)}`}>
              {metrics.regularity_score.toFixed(0)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {getRegularityLabel(metrics.regularity_score)}
            </p>
          </div>
          <Activity className="w-8 h-8 text-green-600" />
        </div>
      </div>

      {/* Current Gap Alert */}
      <div className={`rounded-lg shadow p-4 ${
        currentGap ? 'bg-orange-50 border border-orange-200' : 'bg-white'
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Estado Actual</p>
            {currentGap ? (
              <>
                <p className="text-2xl font-bold text-orange-600">
                  {currentGap.days_since}
                </p>
                <p className="text-xs text-orange-700 mt-1">
                  días sin comprar
                </p>
              </>
            ) : (
              <>
                <p className="text-2xl font-bold text-green-600">OK</p>
                <p className="text-xs text-green-700 mt-1">
                  sin retrasos
                </p>
              </>
            )}
          </div>
          <AlertTriangle className={`w-8 h-8 ${
            currentGap ? 'text-orange-600' : 'text-gray-400'
          }`} />
        </div>
      </div>
    </div>
  );
};

export default FrequencyMetrics;
