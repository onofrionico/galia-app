import api from './api'

// Interruptores del corte con Fudo: catálogo en Galia, Fudo apagado y modo práctica.
const cutoverService = {
  get: async () => (await api.get('/system/cutover')).data,
  update: async (flags) => (await api.put('/system/cutover', flags)).data,
  clearPractice: async () => (await api.post('/system/cutover/clear-practice')).data,
}

export default cutoverService
