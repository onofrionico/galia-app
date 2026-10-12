// Claves de React Query del POS. Las listas se usan como prefijo al invalidar.
export const posKeys = {
  all: ['pos'],
  floors: ['pos', 'floor'],
  floor: (salonId) => ['pos', 'floor', salonId ?? 'default'],
  sales: ['pos', 'sales'],
  counter: ['pos', 'sales', 'counter'],
  sale: (id) => ['pos', 'sale', id],
  events: (id) => ['pos', 'events', id],
  catalog: ['pos', 'catalog'],
  lookup: (name) => ['pos', 'lookup', name],
  config: ['pos', 'config'],
  salons: ['pos', 'config', 'salons'],
  tables: (salonId) => ['pos', 'config', 'tables', salonId],
}
