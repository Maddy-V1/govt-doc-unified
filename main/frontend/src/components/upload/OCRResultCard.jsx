function OCRResultCard({ result }) {
  const getConfidenceColor = (confidence) => {
    if (confidence > 0.7) return 'text-green-600';
    if (confidence > 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBg = (confidence) => {
    if (confidence > 0.7) return 'bg-green-50 border-green-200';
    if (confidence > 0.4) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">OCR Results</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600">OCR Engine</p>
          <p className="font-semibold capitalize">{result.ocr_engine}</p>
        </div>
        
        <div>
          <p className="text-sm text-gray-600">Pages Processed</p>
          <p className="font-semibold">{result.pages_processed}</p>
        </div>
        
        <div>
          <p className="text-sm text-gray-600">Word Count</p>
          <p className="font-semibold">{result.word_count}</p>
        </div>
        
        <div>
          <p className="text-sm text-gray-600">Processing Time</p>
          <p className="font-semibold">{result.processing_time_ms}ms</p>
        </div>
      </div>
      
      <div className={`mt-4 p-4 rounded-lg border ${getConfidenceBg(result.confidence)}`}>
        <p className="text-sm text-gray-600">Confidence Score</p>
        <p className={`text-2xl font-bold ${getConfidenceColor(result.confidence)}`}>
          {(result.confidence * 100).toFixed(1)}%
        </p>
      </div>
      
      <div className="mt-4">
        <p className="text-sm text-gray-600">Chunks Created</p>
        <p className="font-semibold">{result.chunks_created}</p>
      </div>
    </div>
  );
}

export default OCRResultCard;
