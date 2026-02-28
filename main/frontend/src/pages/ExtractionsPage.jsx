import { useState, useEffect } from 'react';
import { extractionsApi } from '../services/extractionsApi';

export default function ExtractionsPage() {
  const [extractions, setExtractions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedExtraction, setSelectedExtraction] = useState(null);
  const [viewingDetails, setViewingDetails] = useState(false);

  useEffect(() => {
    loadExtractions();
  }, []);

  const loadExtractions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await extractionsApi.listExtractions();
      setExtractions(data.extractions || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const viewDetails = async (fileId) => {
    try {
      setLoading(true);
      const details = await extractionsApi.getExtraction(fileId);
      setSelectedExtraction(details);
      setViewingDetails(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (fileId) => {
    if (!confirm('Are you sure you want to delete this extraction?')) return;

    try {
      await extractionsApi.deleteExtraction(fileId);
      setExtractions(extractions.filter(e => e.file_id !== fileId));
      if (selectedExtraction?.file_id === fileId) {
        setSelectedExtraction(null);
        setViewingDetails(false);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'accept': return 'text-green-600 bg-green-50';
      case 'review': return 'text-yellow-600 bg-yellow-50';
      case 'reject': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading && extractions.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading extractions...</p>
        </div>
      </div>
    );
  }

  if (viewingDetails && selectedExtraction) {
    return (
      <div className="container mx-auto px-4 py-8">
        <button
          onClick={() => setViewingDetails(false)}
          className="mb-4 px-4 py-2 text-blue-600 hover:text-blue-800 flex items-center gap-2"
        >
          ← Back to list
        </button>

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{selectedExtraction.filename}</h1>
              <p className="text-sm text-gray-500 mt-1">File ID: {selectedExtraction.file_id}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => extractionsApi.downloadText(selectedExtraction.file_id)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Download Text
              </button>
              {selectedExtraction.ocr.engine === 'paddleocr' && (
                <button
                  onClick={() => extractionsApi.downloadCSV(selectedExtraction.file_id)}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  Download CSV
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">OCR Engine</p>
              <p className="text-lg font-semibold">{selectedExtraction.ocr.engine}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Confidence</p>
              <p className={`text-lg font-semibold ${getConfidenceColor(selectedExtraction.ocr.confidence)}`}>
                {(selectedExtraction.ocr.confidence * 100).toFixed(1)}%
              </p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Word Count</p>
              <p className="text-lg font-semibold">{selectedExtraction.ocr.word_count}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">Pages</p>
              <p className="text-lg font-semibold">{selectedExtraction.ocr.total_pages}</p>
            </div>
          </div>

          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Validation Status</h2>
            <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedExtraction.validation.recommendation)}`}>
              {selectedExtraction.validation.recommendation.toUpperCase()}
            </div>
            {selectedExtraction.validation.warnings?.length > 0 && (
              <div className="mt-2">
                <p className="text-sm font-medium text-gray-700">Warnings:</p>
                <ul className="list-disc list-inside text-sm text-gray-600">
                  {selectedExtraction.validation.warnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {selectedExtraction.ocr.structured_fields && Object.keys(selectedExtraction.ocr.structured_fields).length > 0 && (
            <div className="mb-6">
              <h2 className="text-lg font-semibold mb-2">Structured Fields</h2>
              <div className="bg-gray-50 p-4 rounded-lg">
                <pre className="text-sm overflow-x-auto">
                  {JSON.stringify(selectedExtraction.ocr.structured_fields, null, 2)}
                </pre>
              </div>
            </div>
          )}

          <div>
            <h2 className="text-lg font-semibold mb-2">Extracted Text</h2>
            <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
              <pre className="text-sm whitespace-pre-wrap font-mono">
                {selectedExtraction.ocr.full_text}
              </pre>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Extracted Documents</h1>
        <button
          onClick={loadExtractions}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      {extractions.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600">No extractions found. Upload a document to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {extractions.map((extraction) => (
            <div
              key={extraction.file_id}
              className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {extraction.filename}
                  </h3>
                  
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Engine</p>
                      <p className="font-medium">{extraction.ocr_engine}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Confidence</p>
                      <p className={`font-medium ${getConfidenceColor(extraction.confidence)}`}>
                        {(extraction.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600">Words</p>
                      <p className="font-medium">{extraction.word_count}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Pages</p>
                      <p className="font-medium">{extraction.total_pages}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Status</p>
                      <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getStatusColor(extraction.validation_status)}`}>
                        {extraction.validation_status}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 mt-2">
                    {new Date(extraction.timestamp).toLocaleString()}
                  </p>
                </div>

                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => viewDetails(extraction.file_id)}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                  >
                    View
                  </button>
                  <button
                    onClick={() => extractionsApi.downloadText(extraction.file_id)}
                    className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                  >
                    TXT
                  </button>
                  {extraction.has_csv && (
                    <button
                      onClick={() => extractionsApi.downloadCSV(extraction.file_id)}
                      className="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700"
                    >
                      CSV
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(extraction.file_id)}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
