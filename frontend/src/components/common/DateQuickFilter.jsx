import { useState } from 'react';
import { ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';
import { DEFAULT_PERIOD, monthRangeOf, periodRange, shiftMonth } from '../../utils/monthRange';

const MODES = [
  ['month', 'Por Mes'],
  ['period', 'Período'],
  ['range', 'Rango'],
];

const PERIODS = [
  ['diario', 'Hoy'],
  ['semanal', 'Esta Semana'],
  ['mensual', 'Este Mes'],
  ['trimestral', 'Este Trimestre'],
  ['anual', 'Este Año'],
];

const monthLabel = ({ year, month }) => {
  const name = new Date(year, month - 1, 1).toLocaleDateString('es-AR', { month: 'long' });
  return `${name.charAt(0).toUpperCase()}${name.slice(1)} ${year}`;
};

const nowMonth = () => {
  const now = new Date();
  return { year: now.getFullYear(), month: now.getMonth() + 1 };
};

// Filtro rápido de fechas (mismo esquema que Reportes): por mes, período o rango.
// Informa los cambios con onChange({ from, to }). Para volver a la vista por defecto (hoy) desde afuera,
// remontar el componente cambiándole la `key`.
export default function DateQuickFilter({ from, to, onChange }) {
  const [mode, setMode] = useState('period');
  const [month, setMonth] = useState(nowMonth);
  const [period, setPeriod] = useState(DEFAULT_PERIOD);

  const apply = ({ from: f, to: t }) => onChange(f, t);

  const changeMode = (next) => {
    setMode(next);
    if (next === 'month') apply(monthRangeOf(month));
    if (next === 'period') apply(periodRange(period));
  };

  const goToMonth = (next) => {
    setMonth(next);
    apply(monthRangeOf(next));
  };

  const modeClass = (active) =>
    `px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
      active ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
    }`;

  return (
    <div className="flex flex-wrap items-center gap-4">
      <div className="flex items-center bg-gray-100 rounded-lg p-1">
        {MODES.map(([key, label]) => (
          <button key={key} type="button" onClick={() => changeMode(key)} className={modeClass(mode === key)}>
            {label}
          </button>
        ))}
      </div>

      {mode === 'month' && (
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => goToMonth(shiftMonth(month, -1))} title="Mes anterior"
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <ChevronLeft size={20} />
          </button>
          <div className="px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg min-w-[180px] text-center">
            <span className="text-sm font-semibold text-blue-900">{monthLabel(month)}</span>
          </div>
          <button type="button" onClick={() => goToMonth(shiftMonth(month, 1))} title="Mes siguiente"
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <ChevronRight size={20} />
          </button>
          <button type="button" onClick={() => goToMonth(nowMonth())}
            className="px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors font-medium">
            Mes Actual
          </button>
        </div>
      )}

      {mode === 'period' && (
        <div className="relative">
          <select value={period}
            onChange={(e) => { setPeriod(e.target.value); apply(periodRange(e.target.value)); }}
            className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            {PERIODS.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
        </div>
      )}

      {mode === 'range' && (
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            Desde:
            <input type="date" value={from} onChange={(e) => onChange(e.target.value, to)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-600">
            Hasta:
            <input type="date" value={to} onChange={(e) => onChange(from, e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </label>
        </div>
      )}
    </div>
  );
}
