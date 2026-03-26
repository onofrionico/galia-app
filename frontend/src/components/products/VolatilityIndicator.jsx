import React from 'react';
import { AlertTriangle, TrendingUp, Activity } from 'lucide-react';

const VolatilityIndicator = ({ volatility, size = 'md', showLabel = true }) => {
  const getVolatilityLevel = () => {
    if (volatility < 5) return 'low';
    if (volatility < 15) return 'medium';
    return 'high';
  };

  const getConfig = () => {
    const level = getVolatilityLevel();
    
    const configs = {
      low: {
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        label: 'Baja',
        icon: Activity,
      },
      medium: {
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-200',
        label: 'Media',
        icon: TrendingUp,
      },
      high: {
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        label: 'Alta',
        icon: AlertTriangle,
      },
    };
    
    return configs[level];
  };

  const getSizeClasses = () => {
    const sizes = {
      sm: {
        container: 'px-2 py-1',
        icon: 'w-3 h-3',
        text: 'text-xs',
      },
      md: {
        container: 'px-3 py-1.5',
        icon: 'w-4 h-4',
        text: 'text-sm',
      },
      lg: {
        container: 'px-4 py-2',
        icon: 'w-5 h-5',
        text: 'text-base',
      },
    };
    
    return sizes[size] || sizes.md;
  };

  const config = getConfig();
  const sizeClasses = getSizeClasses();
  const Icon = config.icon;

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-lg border ${config.bgColor} ${config.borderColor} ${sizeClasses.container}`}
    >
      <Icon className={`${config.color} ${sizeClasses.icon}`} />
      <div className="flex items-center gap-1.5">
        {showLabel && (
          <span className={`font-medium ${config.color} ${sizeClasses.text}`}>
            {config.label}
          </span>
        )}
        <span className={`font-semibold ${config.color} ${sizeClasses.text}`}>
          {volatility.toFixed(1)}%
        </span>
      </div>
    </div>
  );
};

export default VolatilityIndicator;
