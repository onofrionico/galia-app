import axios from 'axios'
import { API_BASE_URL, getAuthHeader, getJsonHeader } from '@/config/api'

const biometricService = {
  /**
   * Generate a QR code for biometric check-in
   * @returns {Promise} { qr_code, token, employee_id, employee_name, expires_at }
   */
  generateQR: async () => {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/biometric/qr-generate`,
      {},
      { headers: getAuthHeader() }
    )
    return response.data
  },

  /**
   * Validate a QR code token
   * @param {string} token - QR token
   * @returns {Promise} { valid, employee_id, employee_name, session_token }
   */
  validateQRToken: async (token) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/biometric/qr/${token}`
      )
      return response.data
    } catch (error) {
      const message = error.response?.data?.error || error.message || 'QR inválido'
      throw new Error(message)
    }
  },

  /**
   * Register a biometric check-in
   * @param {Object} data - Check-in data
   *   - qr_token: string
   *   - entry_type: 'in' or 'out'
   *   - photo_base64: base64-encoded image
   *   - latitude: number
   *   - longitude: number
   *   - accuracy: number (GPS accuracy in meters)
   *   - biometric_confidence: number (0-1)
   *   - biometric_verified: boolean
   * @returns {Promise} { success, message, work_block_id, timestamp, entry_type }
   */
  checkIn: async (data) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/biometric/check-in`,
        data,
        { headers: getJsonHeader() }
      )
      return response.data
    } catch (error) {
      const message = error.response?.data?.error || error.message || 'Error al registrar entrada'
      throw new Error(message)
    }
  },

  /**
   * Verify facial recognition
   * @param {Object} data - Verification data
   *   - photo_base64: base64-encoded current photo
   *   - stored_photo_url: URL to stored profile photo (optional)
   * @returns {Promise} { verified, confidence, threshold }
   */
  verifyFace: async (data) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/biometric/verify-face`,
        data,
        { headers: getJsonHeader() }
      )
      return response.data
    } catch (error) {
      const message = error.response?.data?.error || error.message || 'Error al verificar rostro'
      throw new Error(message)
    }
  },
}

export default biometricService
