import api from './api';

const employeeDocumentsService = {
  async getMyDocuments(params = {}) {
    const response = await api.get('/my-documents', { params });
    return response.data;
  },

  async getMyPayrolls(params = {}) {
    const response = await api.get('/my-documents/payrolls', { params });
    return response.data;
  },

  async getMySocialSecurity(params = {}) {
    const response = await api.get('/my-documents/social-security', { params });
    return response.data;
  },

  async getMyAbsences(params = {}) {
    const response = await api.get('/my-documents/absences', { params });
    return response.data;
  },

  async downloadDocument(documentType, documentId) {
    const url = `/my-documents/download/${documentType}/${documentId}`;
    console.log('Llamando a URL de descarga:', url);
    const response = await api.get(url, {
      responseType: 'blob'
    });
    return response.data;
  }
};

export default employeeDocumentsService;
