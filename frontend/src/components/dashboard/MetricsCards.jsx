import React from 'react';
import { DollarSign, ShoppingCart, TrendingUp, Users } from 'lucide-react';

const MetricsCards = ({ metrics }) => {
  const cards = [
    {
      title: 'Total Gastado',
      value: `$${metrics.total_spent.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      icon: DollarSign,
      change: metrics.spending_change,
      changeLabel: 'vs período anterior',
      color: 'blue',
    },
    {
      title: 'Total Compras',
      value: metrics.total_purchases,
      icon: ShoppingCart,
      color: 'green',
    },
    {
      title: 'Valor Promedio',
      value: `$${metrics.avg_order_value.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      icon: TrendingUp,
      color: 'purple',
    },
    {
      title: 'Proveedores Activos',
      value: metrics.unique_suppliers,
      icon: Users,
      color: 'orange',
    },
  ];

  const getColorClasses = (color) => {
    const colors = {
      blue: 'bg-blue-50 text-blue-600',
      green: 'bg-green-50 text-green-600',
      purple: 'bg-purple-50 text-purple-600',
      orange: 'bg-orange-50 text-orange-600',
    };
    return colors[color] || colors.blue;
  };

  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900 mt-2">{card.value}</p>
                {card.change !== undefined && (
                  <p className={`text-sm mt-2 ${getChangeColor(card.change)}`}>
                    {card.change > 0 ? '+' : ''}{card.change.toFixed(1)}% {card.changeLabel}
                  </p>
                )}
              </div>
              <div className={`p-3 rounded-lg ${getColorClasses(card.color)}`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default MetricsCards;
