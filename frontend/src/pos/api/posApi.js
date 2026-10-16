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

export const posCashApi = {
  registers: () => data(api.get('/pos/cash/registers')).then((d) => d.registers),
  session: (id) => data(api.get(`/pos/cash/sessions/${id}`)),
  open: (body) => data(api.post('/pos/cash/sessions', body)),
  addMovement: (id, body) => data(api.post(`/pos/cash/sessions/${id}/movements`, body)),
  cancelMovement: (movementId, reason) => data(api.post(`/pos/cash/movements/${movementId}/cancel`, { reason })),
  close: (id, body) => data(api.post(`/pos/cash/sessions/${id}/close`, body)),
  reopen: (id, reason) => data(api.post(`/pos/cash/sessions/${id}/reopen`, { reason })),
  listSessions: (params) => data(api.get('/pos/cash/sessions', { params })),
  unassignedPayments: (params) => data(api.get('/pos/cash/unassigned-payments', { params })).then((d) => d.payments),
  expenseCategories: () => data(api.get('/pos/cash/expense-categories')).then((d) => d.categories),
}

// Catálogos simples de /pos/config: recurso de la URL → clave de la respuesta.
const RESOURCE_KEYS = {
  'payment-methods': 'payment_methods',
  'discount-templates': 'discount_templates',
  'cancel-reasons': 'cancel_reasons',
  'print-stations': 'print_stations',
  printers: 'printers',
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

export const posPrintApi = {
  printBill: (saleId) => data(api.post(`/pos/sales/${saleId}/print/bill`)),
  printReceipt: (saleId) => data(api.post(`/pos/sales/${saleId}/print/receipt`)),
  reprint: (jobId) => data(api.post(`/pos/print/jobs/${jobId}/reprint`)),
  saleJobs: (saleId) => data(api.get(`/pos/sales/${saleId}/print-jobs`)).then((d) => d.jobs),
  claim: (point) => data(api.post('/pos/print/claim', { print_point: point })).then((d) => d.jobs),
  done: (jobId) => data(api.post(`/pos/print/jobs/${jobId}/done`)),
  failed: (jobId, error) => data(api.post(`/pos/print/jobs/${jobId}/failed`, { error })),
  retry: (jobId) => data(api.post(`/pos/print/jobs/${jobId}/retry`)),
  markPrinted: (jobId) => data(api.post(`/pos/print/jobs/${jobId}/mark-printed`)),
  status: () => data(api.get('/pos/print/status')),
  points: () => data(api.get('/pos/print/points')).then((d) => d.points),
  testPrint: (printerId) => data(api.post(`/pos/print/printers/${printerId}/test`)),
  qzCertificate: () => data(api.get('/pos/print/qz-certificate')).then((d) => d.certificate),
  qzSign: (request) => data(api.post('/pos/print/qz-sign', { request })).then((d) => d.signature),
  qzSetup: () => data(api.get('/pos/print/qz-setup', { responseType: 'blob' })),
  stations: () => data(api.get('/pos/print/stations')).then((d) => d.stations),
}

export const posFiscalApi = {
  preview: (saleId) => data(api.get(`/fiscal/sales/${saleId}/preview`)),
  issue: (saleId, customer) => data(api.post(`/fiscal/sales/${saleId}/invoice`, { customer })),
  saleInvoices: (saleId) => data(api.get(`/fiscal/sales/${saleId}/invoices`)).then((d) => d.invoices),
  verify: (id) => data(api.post(`/fiscal/invoices/${id}/verify`)),
  cancel: (id) => data(api.post(`/fiscal/invoices/${id}/cancel`)),
  reprint: (id) => data(api.post(`/fiscal/invoices/${id}/reprint`)),
  list: (params) => data(api.get('/fiscal/invoices', { params })),
  get: (id) => data(api.get(`/fiscal/invoices/${id}`)),
  customers: (q) => data(api.get('/fiscal/customers', { params: { q } })).then((d) => d.customers),
  settings: () => data(api.get('/fiscal/settings')),
  saveSettings: (body) => data(api.put('/fiscal/settings', body)),
  generateCsr: (env) => data(api.post(`/fiscal/settings/${env}/csr`)).then((d) => d.csr),
  saveCertificate: (env, certificate) => data(api.put(`/fiscal/settings/${env}/certificate`, { certificate })),
  testConnection: () => data(api.post('/fiscal/settings/test')),
}

export const posMpApi = {
  pointConfig: () => data(api.get('/mp/point-config')),
  startPoint: (saleId, amount) => data(api.post(`/mp/sales/${saleId}/point`, { amount })),
  pointOrder: (id) => data(api.get(`/mp/point-orders/${id}`)),
  cancelPoint: (id) => data(api.post(`/mp/point-orders/${id}/cancel`)),
  salePointOrders: (saleId) => data(api.get(`/mp/sales/${saleId}/point-orders`)).then((d) => d.orders),
  fakePoint: (id, outcome) => data(api.post(`/mp/fake/point-orders/${id}/${outcome}`)),
  reconciliationSummary: (from, to) => data(api.get('/mp/reconciliation', { params: { from, to } })).then((d) => d.days),
  reconciliationDay: (day) => data(api.get(`/mp/reconciliation/${day}`)),
  fetchDay: (day) => data(api.post(`/mp/reconciliation/${day}/fetch`)),
  resolve: (body) => data(api.post('/mp/reconciliation/resolutions', body)),
  undo: (id) => data(api.delete(`/mp/reconciliation/resolutions/${id}`)),
  settings: () => data(api.get('/mp/settings')),
  saveSettings: (body) => data(api.put('/mp/settings', body)),
  saveToken: (environment, accessToken) => data(api.put('/mp/settings/token', { environment, access_token: accessToken })),
  terminals: () => data(api.get('/mp/settings/terminals')).then((d) => d.terminals),
  setPdv: (id) => data(api.post(`/mp/settings/terminals/${id}/pdv`)),
  testConnection: () => data(api.post('/mp/settings/test')),
}
