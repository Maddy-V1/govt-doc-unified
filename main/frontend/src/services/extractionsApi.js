/**
 * API service for extracted documents
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const extractionsApi = {
  /**
   * List all extractions
   */
  async listExtractions(limit = 100, offset = 0) {
    const response = await fetch(
      `${API_BASE_URL}/extractions?limit=${limit}&offset=${offset}`
    );
    
    if (!response.ok) {
      throw new Error(`Failed to fetch extractions: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Get full extraction details
   */
  async getExtraction(fileId) {
    const response = await fetch(`${API_BASE_URL}/extractions/${fileId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch extraction: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Download extracted text
   */
  downloadText(fileId) {
    window.open(`${API_BASE_URL}/extractions/${fileId}/text`, '_blank');
  },

  /**
   * Download extracted CSV (if available)
   */
  downloadCSV(fileId) {
    window.open(`${API_BASE_URL}/extractions/${fileId}/csv`, '_blank');
  },

  /**
   * Delete extraction
   */
  async deleteExtraction(fileId) {
    const response = await fetch(`${API_BASE_URL}/extractions/${fileId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`Failed to delete extraction: ${response.statusText}`);
    }
    
    return response.json();
  },
};
