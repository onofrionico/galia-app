import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { useNavigate } from 'react-router-dom';

const TopSuppliersChart = ({ data }) => {
  const navigate = useNavigate();

  const COLORS = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16'
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900">{data.name}</p>
          <p className="text-sm text-gray-600 mt-1">
            Total: ${data.total_spent.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
          </p>
          <p className="text-sm text-gray-600">
            Compras: {data.purchase_count}
          </p>
          <p className="text-sm text-gray-600">
            Promedio: ${data.avg_order_value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
          </p>
          <p className="text-sm text-blue-600 font-medium mt-1">
            {data.percentage}% del total
          </p>
        </div>
      );
    }
    return null;
  };

  const handleBarClick = (data) => {
    if (data && data.id) {
      navigate(`/suppliers/${data.id}`);
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Proveedores</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          No hay datos disponibles
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Proveedores por Gasto</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 80 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={100}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="total_spent"
            radius={[8, 8, 0, 0]}
            cursor="pointer"
            onClick={handleBarClick}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TopSuppliersChart;
