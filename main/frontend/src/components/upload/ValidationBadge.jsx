function ValidationBadge({ validation }) {
  const getBadgeStyle = () => {
    switch (validation.recommendation) {
      case 'store':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'review':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'reject':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getBadgeText = () => {
    switch (validation.recommendation) {
      case 'store':
        return 'Ready';
      case 'review':
        return 'Needs Review';
      case 'reject':
        return 'Rejected';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">Validation Status</h3>
      
      <div className={`inline-block px-4 py-2 rounded-full border-2 font-semibold ${getBadgeStyle()}`}>
        {getBadgeText()}
      </div>
      
      {validation.warnings && validation.warnings.length > 0 && (
        <div className="mt-4">
          <p className="font-semibold text-gray-700 mb-2">Warnings:</p>
          <ul className="list-disc list-inside space-y-1">
            {validation.warnings.map((warning, index) => (
              <li key={index} className="text-sm text-gray-600">
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
        <div className="flex items-center">
          <span className={`mr-2 ${validation.confidence_ok ? 'text-green-600' : 'text-red-600'}`}>
            {validation.confidence_ok ? '✓' : '✗'}
          </span>
          <span>Confidence OK</span>
        </div>
        <div className="flex items-center">
          <span className={`mr-2 ${validation.has_text ? 'text-green-600' : 'text-red-600'}`}>
            {validation.has_text ? '✓' : '✗'}
          </span>
          <span>Has Text</span>
        </div>
      </div>
    </div>
  );
}

export default ValidationBadge;
