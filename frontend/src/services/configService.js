import api from './api'

const configService = {
  async getBrandingConfig() {
    try {
      const response = await api.get('/config/branding')
      return response.data
    } catch (error) {
      throw new Error('Failed to fetch branding config: ' + error.message)
    }
  },

  async updateBrandingConfig(logoFile, backgroundFile) {
    try {
      const formData = new FormData()
      if (logoFile) formData.append('logo', logoFile)
      if (backgroundFile) formData.append('background', backgroundFile)

      const response = await api.post('/admin/config/branding', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } catch (error) {
      throw new Error('Failed to update branding config: ' + error.message)
    }
  }
}

export default configService
