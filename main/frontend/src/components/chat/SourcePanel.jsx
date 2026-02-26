import { useState } from 'react';

function SourcePanel({ sources }) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="bg-white rounded-lg shadow h-full flex flex-col">
      <div 
        className="p-4 border-b cursor-pointer flex justify-between items-center"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className="font-semibold">Sources ({sources.length})</h3>
        <button className="text-gray-500">
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>
      
      {isExpanded && (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {sources.map((source, index) => (
            <div key={index} className="border rounded-lg p-3 bg-gray-50">
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-semibold text-blue-600">
                  Source {index + 1}
                </span>
                {source.similarity_score !== undefined && (
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {(source.similarity_score * 100).toFixed(1)}%
                  </span>
                )}
              </div>
              
              <p className="text-sm text-gray-700 mb-2">
                {source.chunk?.chunk_text?.substring(0, 200) || source.chunk?.text?.substring(0, 200) || ''}
                {(source.chunk?.chunk_text?.length > 200 || source.chunk?.text?.length > 200) && '...'}
              </p>
              
              {source.chunk?.metadata && (
                <div className="text-xs text-gray-500 space-y-1">
                  {source.chunk.metadata.filename && (
                    <p>File: {source.chunk.metadata.filename}</p>
                  )}
                  {source.chunk.metadata.page_number && (
                    <p>Page: {source.chunk.metadata.page_number}</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SourcePanel;
