export const RUN_STATS = [
  ['fetched', 'Obtenidos de Fudo'],
  ['created', 'Nuevos'],
  ['updated', 'Actualizados'],
  ['unchanged', 'Sin cambios'],
  ['suppliers_created', 'Proveedores nuevos'],
  ['suppliers_linked', 'Proveedores vinculados'],
  ['categories_created', 'Categorías nuevas'],
  ['categories_linked', 'Categorías vinculadas'],
];

const MAX_RANGE_DAYS = 366;
const DAY_MS = 24 * 60 * 60 * 1000;

export const isRunFinished = (run) => Boolean(run) && run.status !== 'running';

export const summarizeRun = (run) =>
  RUN_STATS.map(([key, label]) => ({ key, label, value: run?.stats?.[key] ?? 0 }));

export const validateRange = (start, end) => {
  if (!start || !end) return 'Elegí las dos fechas';
  if (start > end) return 'La fecha "Desde" no puede ser posterior a "Hasta"';
  if ((Date.parse(end) - Date.parse(start)) / DAY_MS > MAX_RANGE_DAYS) {
    return `El rango no puede superar ${MAX_RANGE_DAYS} días`;
  }
  return null;
};

export const formatRunDate = (iso) =>
  (iso ? new Date(`${iso}Z`).toLocaleString('es-AR', { hourCycle: 'h23' }) : '-');
