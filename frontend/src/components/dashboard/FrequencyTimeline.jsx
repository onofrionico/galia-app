import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Calendar, AlertCircle } from 'lucide-react';

const FrequencyTimeline = ({ timeline, gaps, avgDaysBetween }) => {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500 text-center">No hay datos de compras disponibles</p>
      </div>
    );
  }

  // Prepare data for chart - calculate days between purchases
  const chartData = timeline.map((purchase, index) => {
    let daysSinceLast = 0;
    if (index > 0) {
      const prevDate = new Date(timeline[index - 1].date);
      const currDate = new Date(purchase.date);
      daysSinceLast = Math.floor((currDate - prevDate) / (1000 * 60 * 60 * 24));
    }

    return {
      date: new Date(purchase.date).toLocaleDateString('es-AR', { 
        day: '2-digit', 
        month: 'short' 
      }),
      fullDate: purchase.date,
      daysSinceLast,
      amount: purchase.total_amount,
      purchaseId: purchase.purchase_id,
      isGap: daysSinceLast > avgDaysBetween * 1.5
    };
  });

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="font-semibold text-gray-900">
            {new Date(data.fullDate).toLocaleDateString('es-AR')}
          </p>
          {data.daysSinceLast > 0 && (
            <p className={`text-sm ${data.isGap ? 'text-orange-600 font-semibold' : 'text-gray-600'}`}>
              {data.daysSinceLast} días desde la anterior
            </p>
          )}
          <p className="text-sm text-gray-600">
            Monto: ${data.amount.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Timeline de Compras
        </h3>
        {gaps && gaps.length > 0 && (
          <div className="flex items-center gap-2 text-orange-600">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm font-medium">{gaps.length} gap(s) detectado(s)</span>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              label={{ value: 'Días entre compras', angle: -90, position: 'insideLeft' }}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine 
              y={avgDaysBetween} 
              stroke="#6366f1" 
              strokeDasharray="3 3"
              label={{ value: 'Promedio', position: 'right', fill: '#6366f1', fontSize: 12 }}
            />
            <ReferenceLine 
              y={avgDaysBetween * 1.5} 
              stroke="#f59e0b" 
              strokeDasharray="3 3"
              label={{ value: 'Umbral gap', position: 'right', fill: '#f59e0b', fontSize: 12 }}
            />
            <Bar 
              dataKey="daysSinceLast" 
              fill="#3b82f6"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Gaps List */}
      {gaps && gaps.length > 0 && (
        <div className="border-t pt-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Gaps Detectados</h4>
          <div className="space-y-2">
            {gaps.map((gap, index) => (
              <div 
                key={index}
                className="flex items-center justify-between p-3 bg-orange-50 border border-orange-200 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <AlertCircle className="w-4 h-4 text-orange-600" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {new Date(gap.start_date).toLocaleDateString('es-AR')} - {new Date(gap.end_date).toLocaleDateString('es-AR')}
                    </p>
                    <p className="text-xs text-gray-600">
                      {gap.days} días (esperado: ~{gap.expected_days} días)
                    </p>
                  </div>
                </div>
                <span className="text-sm font-semibold text-orange-600">
                  +{(gap.days - gap.expected_days).toFixed(0)} días
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="border-t pt-4 mt-4">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-gray-600">Primera Compra</p>
            <p className="text-sm font-semibold text-gray-900">
              {new Date(timeline[0].date).toLocaleDateString('es-AR')}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Última Compra</p>
            <p className="text-sm font-semibold text-gray-900">
              {new Date(timeline[timeline.length - 1].date).toLocaleDateString('es-AR')}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600">Total Compras</p>
            <p className="text-sm font-semibold text-gray-900">
              {timeline.length}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FrequencyTimeline;
