import api from './api'

const data = (request) => request.then((response) => response.data)

// El cliente axios ya tiene /api/v1 como base.
const voucherService = {
  listBatches: () => data(api.get('/vouchers/batches')),
  getBatch: (id) => data(api.get(`/vouchers/batches/${id}`)),
  createBatch: (body) => data(api.post('/vouchers/batches', body)),
  extendExpiry: (id, expiresAt) => data(api.put(`/vouchers/batches/${id}`, { expires_at: expiresAt })),
  voidVoucher: (id, reason) => data(api.post(`/vouchers/${id}/void`, { reason })),
}

export default voucherService
