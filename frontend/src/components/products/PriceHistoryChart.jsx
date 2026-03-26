import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const PriceHistoryChart = ({ data, analysis }) => {
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900">
            {new Date(data.effective_date).toLocaleDateString('es-AR')}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            Precio: ${data.price.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
          </p>
          {data.change_percentage !== 0 && (
            <p className={`text-sm font-medium ${data.change_percentage > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {data.change_percentage > 0 ? '+' : ''}{data.change_percentage.toFixed(2)}%
            </p>
          )}
          {data.source && (
            <p className="text-xs text-gray-500 mt-1">
              Origen: {data.source}
            </p>
          )}
          {data.notes && (
            <p className="text-xs text-gray-500 italic mt-1">
              {data.notes}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  const getTrendIcon = () => {
    if (!analysis) return null;
    
    switch (analysis.trend) {
      case 'increasing':
        return <TrendingUp className="w-5 h-5 text-green-600" />;
      case 'decreasing':
        return <TrendingDown className="w-5 h-5 text-red-600" />;
      default:
        return <Minus className="w-5 h-5 text-gray-600" />;
    }
  };

  const getTrendColor = () => {
    if (!analysis) return 'text-gray-600';
    
    switch (analysis.trend) {
      case 'increasing':
        return 'text-green-600';
      case 'decreasing':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTrendLabel = () => {
    if (!analysis) return 'Sin datos';
    
    switch (analysis.trend) {
      case 'increasing':
        return 'Tendencia al alza';
      case 'decreasing':
        return 'Tendencia a la baja';
      default:
        return 'Estable';
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Historial de Precios</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          No hay historial de precios disponible
        </div>
      </div>
    );
  }

  // Reverse data to show oldest to newest
  const chartData = [...data].reverse();

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Historial de Precios</h3>
          <p className="text-sm text-gray-600 mt-1">
            {data.length} cambios de precio registrados
          </p>
        </div>
        {analysis && (
          <div className="flex items-center gap-2">
            {getTrendIcon()}
            <span className={`text-sm font-medium ${getTrendColor()}`}>
              {getTrendLabel()}
            </span>
          </div>
        )}
      </div>

      {/* Analysis Summary */}
      {analysis && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600">Precio Promedio</p>
            <p className="text-lg font-semibold text-gray-900">
              ${analysis.avg_price.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600">Precio Mínimo</p>
            <p className="text-lg font-semibold text-green-600">
              ${analysis.min_price.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600">Precio Máximo</p>
            <p className="text-lg font-semibold text-red-600">
              ${analysis.max_price.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600">Volatilidad</p>
            <p className="text-lg font-semibold text-orange-600">
              {analysis.volatility.toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="effective_date"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => {
              const date = new Date(value);
              return `${date.getDate()}/${date.getMonth() + 1}`;
            }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `$${value.toLocaleString('es-AR')}`}
            domain={['dataMin - 100', 'dataMax + 100']}
          />
          <Tooltip content={<CustomTooltip />} />
          {analysis && (
            <>
              <ReferenceLine
                y={analysis.avg_price}
                stroke="#6B7280"
                strokeDasharray="3 3"
                label={{ value: 'Promedio', position: 'right', fill: '#6B7280', fontSize: 12 }}
              />
            </>
          )}
          <Line
            type="monotone"
            dataKey="price"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={{ fill: '#3B82F6', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Additional Info */}
      {analysis && (
        <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
          <div>
            Cambio promedio: <span className="font-medium">{analysis.avg_change_percentage.toFixed(2)}%</span>
          </div>
          {analysis.last_change_days !== null && (
            <div>
              Último cambio hace: <span className="font-medium">{analysis.last_change_days} días</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PriceHistoryChart;
