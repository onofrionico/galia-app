import axios from 'axios'

const API_BASE_URL = '/api/v1'

export const configService = {
  getBrandingConfig: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/config/branding`)
      return response.data
    } catch (error) {
      console.error('Error fetching branding config:', error)
      return {
        logo_path: null,
        banner_background_path: null
      }
    }
  },

  updateBrandingConfig: async (logoFile, backgroundFile) => {
    try {
      const formData = new FormData()
      if (logoFile) formData.append('logo', logoFile)
      if (backgroundFile) formData.append('background', backgroundFile)

      const response = await axios.post(`${API_BASE_URL}/admin/config/branding`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } catch (error) {
      console.error('Error updating branding config:', error)
      throw error
    }
  }
}

export default configService
