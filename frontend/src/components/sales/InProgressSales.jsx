import { useEffect, useState } from 'react';
import api from '../../services/api';
import MoneyFormat from '../MoneyFormat';

const POLL_MS = 30000;

const STATUS = {
  open: { label: 'Abierta', className: 'bg-amber-100 text-amber-800' },
  billing: { label: 'Cuenta pedida', className: 'bg-rose-100 text-rose-800' },
};

const openedAt = (iso) =>
  new Date(iso).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Argentina/Buenos_Aires' });

// Ventas del POS que todavía no cerraron. Solo lectura y aparte de la tabla: no están en `sales`,
// así que no cuentan en las estadísticas ni en la exportación hasta que se cierren.
export default function InProgressSales({ refreshKey = 0 }) {
  const [data, setData] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const response = await api.get('/sales/in-progress');
        if (active) { setData(response.data); setFailed(false); }
      } catch {
        if (active) setFailed(true);
      }
    };
    load();
    const timer = setInterval(load, POLL_MS);
    return () => { active = false; clearInterval(timer); };
  }, [refreshKey]);

  if (!data) {
    return failed ? <p className="mb-6 text-sm text-gray-500">No se pudieron cargar las ventas en curso.</p> : null;
  }

  return (
    <div className="bg-white rounded-lg shadow mb-6">
      <div className="p-4 border-b flex items-center justify-between">
        <h2 className="font-semibold text-gray-900">
          En curso ahora <span className="text-gray-500 font-normal">({data.sales.length})</span>
        </h2>
        <span className="font-semibold text-gray-900">$<MoneyFormat amount={data.total} /></span>
      </div>
      {data.sales.length === 0 ? (
        <p className="p-4 text-sm text-gray-500">No hay ventas en curso.</p>
      ) : (
        <ul className="divide-y">
          {data.sales.map((sale) => {
            const status = STATUS[sale.status] ?? STATUS.open;
            return (
              <li key={sale.id} className="px-4 py-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                <span className="font-medium text-gray-900 min-w-[150px]">{sale.place}</span>
                <span className={`px-2 py-0.5 rounded-full text-xs ${status.className}`}>{status.label}</span>
                <span className="text-gray-600">#{sale.number}</span>
                <span className="text-gray-600">{sale.waiter ?? '—'}</span>
                {sale.people ? <span className="text-gray-600">{sale.people} pers.</span> : null}
                <span className="text-gray-600">abierta {openedAt(sale.opened_at)}</span>
                <span className="ml-auto font-medium text-gray-900">$<MoneyFormat amount={sale.total} /></span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
