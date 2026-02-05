import api from './api'

export const jobPositionService = {
  async getJobPositions(params = {}) {
    const response = await api.get('/job-positions', { params })
    return response.data
  },

  async getJobPosition(id) {
    const response = await api.get(`/job-positions/${id}`)
    return response.data
  },

  async createJobPosition(positionData) {
    const response = await api.post('/job-positions', positionData)
    return response.data
  },

  async updateJobPosition(id, positionData) {
    const response = await api.put(`/job-positions/${id}`, positionData)
    return response.data
  },

  async deactivateJobPosition(id) {
    const response = await api.patch(`/job-positions/${id}/deactivate`)
    return response.data
  },

  async activateJobPosition(id) {
    const response = await api.patch(`/job-positions/${id}/activate`)
    return response.data
  },
}
