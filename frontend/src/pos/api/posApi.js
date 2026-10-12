import api from '@/services/api'

const data = (request) => request.then((response) => response.data)

export const posApi = {
  getFloor: (salonId) => data(api.get('/pos/floor', { params: salonId ? { salon_id: salonId } : {} })),
  getCatalog: () => data(api.get('/pos/catalog')),
  getChanges: (since) => data(api.get('/pos/changes', { params: since == null ? {} : { since } })),
  listSales: (params) => data(api.get('/pos/sales', { params })).then((d) => d.sales),
  getSale: (id) => data(api.get(`/pos/sales/${id}`)),
  getEvents: (id) => data(api.get(`/pos/sales/${id}/events`)).then((d) => d.events),
  openSale: (body) => data(api.post('/pos/sales', body)),
  addItem: (id, body) => data(api.post(`/pos/sales/${id}/items`, body)),
  deleteItem: (id, itemId) => data(api.delete(`/pos/sales/${id}/items/${itemId}`)),
  confirm: (id) => data(api.post(`/pos/sales/${id}/confirm`)),
  cancelItem: (id, itemId, body) => data(api.post(`/pos/sales/${id}/items/${itemId}/cancel`, body)),
  requestBill: (id) => data(api.post(`/pos/sales/${id}/request-bill`)),
  reopen: (id) => data(api.post(`/pos/sales/${id}/reopen`)),
  addDiscount: (id, body) => data(api.post(`/pos/sales/${id}/discounts`, body)),
  cancelDiscount: (discountId) => data(api.post(`/pos/discounts/${discountId}/cancel`)),
  addPayment: (id, body) => data(api.post(`/pos/sales/${id}/payments`, body)),
  cancelPayment: (paymentId, body) => data(api.post(`/pos/payments/${paymentId}/cancel`, body)),
  close: (id) => data(api.post(`/pos/sales/${id}/close`)),
  move: (id, tableId) => data(api.post(`/pos/sales/${id}/move`, { table_id: tableId })),
  split: (id, items) => data(api.post(`/pos/sales/${id}/split`, { items })),
  cancelSale: (id, body) => data(api.post(`/pos/sales/${id}/cancel`, body)),
  changeWaiter: (id, waiterId) => data(api.post(`/pos/sales/${id}/waiter`, { waiter_id: waiterId })),
  getWaiters: () => data(api.get('/pos/waiters')).then((d) => d.waiters),
  getCancelReasons: () => data(api.get('/pos/cancel-reasons')).then((d) => d.cancel_reasons),
  getPaymentMethods: () => data(api.get('/pos/payment-methods')).then((d) => d.payment_methods),
  getDiscountTemplates: () => data(api.get('/pos/discount-templates')).then((d) => d.discount_templates),
}

// Catálogos simples de /pos/config: recurso de la URL → clave de la respuesta.
const RESOURCE_KEYS = {
  'payment-methods': 'payment_methods',
  'discount-templates': 'discount_templates',
  'cancel-reasons': 'cancel_reasons',
}

export const posConfigApi = {
  listSalons: () => data(api.get('/pos/config/salons')).then((d) => d.salons),
  createSalon: (body) => data(api.post('/pos/config/salons', body)),
  updateSalon: (id, body) => data(api.put(`/pos/config/salons/${id}`, body)),
  listTables: (salonId) => data(api.get('/pos/config/tables', { params: { salon_id: salonId } })).then((d) => d.tables),
  createTable: (body) => data(api.post('/pos/config/tables', body)),
  updateTable: (id, body) => data(api.put(`/pos/config/tables/${id}`, body)),
  listModifierGroups: () => data(api.get('/pos/config/modifier-groups')).then((d) => d.modifier_groups),
  createModifierGroup: (body) => data(api.post('/pos/config/modifier-groups', body)),
  updateModifierGroup: (id, body) => data(api.put(`/pos/config/modifier-groups/${id}`, body)),
  getProductModifierGroups: (productId) =>
    data(api.get(`/pos/config/products/${productId}/modifier-groups`)).then((d) => d.group_ids),
  setProductModifierGroups: (productId, groupIds) =>
    data(api.put(`/pos/config/products/${productId}/modifier-groups`, { group_ids: groupIds })),
  listResource: (resource) => data(api.get(`/pos/config/${resource}`)).then((d) => d[RESOURCE_KEYS[resource]]),
  createResource: (resource, body) => data(api.post(`/pos/config/${resource}`, body)),
  updateResource: (resource, id, body) => data(api.put(`/pos/config/${resource}/${id}`, body)),
}
