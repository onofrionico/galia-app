import api from './api'

const API_PREFIX = '/api/v1'
const ADMIN = '/loyalty/admin'
const data = (request) => request.then((response) => response.data)

export function reportsUrl(name, range = null) {
  const base = `${API_PREFIX}${ADMIN}/reports/${name}`
  if (!range) return base
  return `${base}?${new URLSearchParams({ from: range.from, to: range.to }).toString()}`
}

const pad = (n) => String(n).padStart(2, '0')

// '2026-02' → { from: '2026-02-01', to: '2026-02-28' }
export function monthRange(month) {
  const [year, m] = month.split('-').map(Number)
  const last = new Date(Date.UTC(year, m, 0)).getUTCDate()
  return { from: `${year}-${pad(m)}-01`, to: `${year}-${pad(m)}-${pad(last)}` }
}

// El cliente axios ya tiene /api/v1 como base.
const report = (name, range) => data(api.get(reportsUrl(name, range).slice(API_PREFIX.length)))

const loyaltyService = {
  getSettings: () => data(api.get(`${ADMIN}/settings`)),
  updateSettings: (activeDays) => data(api.put(`${ADMIN}/settings`, { active_days: activeDays })),
  listRewards: () => data(api.get(`${ADMIN}/rewards`)),
  createReward: (body) => data(api.post(`${ADMIN}/rewards`, body)),
  updateReward: (id, body) => data(api.put(`${ADMIN}/rewards/${id}`, body)),
  listVariants: (q) => data(api.get(`${ADMIN}/variants`, { params: q ? { q } : {} })),
  setVariantCafecitos: (variantIds, cafecitos) => data(api.put(`${ADMIN}/variants/cafecitos`, {
    variant_ids: variantIds, cafecitos,
  })),
  listCustomers: (q) => data(api.get(`${ADMIN}/customers`, { params: q ? { q } : {} })),
  getCustomer: (id) => data(api.get(`${ADMIN}/customers/${id}`)),
  adjust: (id, amount, reason) => data(api.post(`${ADMIN}/customers/${id}/adjustments`, { amount, reason })),
  regenerateQr: (id) => data(api.post(`${ADMIN}/customers/${id}/regenerate-qr`)),
  changeLog: (entity) => data(api.get(`${ADMIN}/change-log`, { params: entity ? { entity } : {} })),
  activeReport: () => report('active'),
  inactiveReport: () => report('inactive'),
  redemptionsReport: (range) => report('redemptions', range),
  salesComparisonReport: (range) => report('sales-comparison', range),
}

export default loyaltyService
