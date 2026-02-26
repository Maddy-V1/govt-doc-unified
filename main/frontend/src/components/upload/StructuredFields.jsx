function StructuredFields({ fields }) {
  if (!fields || Object.keys(fields).length === 0) {
    return null;
  }

  const formatValue = (value) => {
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const fieldLabels = {
    document_type: 'Document Type',
    ddo_code: 'DDO Code',
    account_number: 'Account Number',
    month_year: 'Month/Year',
    month: 'Month',
    year: 'Year',
    grand_total: 'Grand Total',
    dates_found: 'Dates Found',
    officers_mentioned: 'Officers',
    officers: 'Officers',
    head_of_account_codes: 'HoA Codes',
    hoa_codes: 'HoA Codes',
    balance_validation: 'Balance Validation'
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">Structured Fields</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(fields).map(([key, value]) => {
          if (!value || (Array.isArray(value) && value.length === 0)) {
            return null;
          }
          
          return (
            <div key={key} className="border-b pb-2">
              <p className="text-sm text-gray-600 font-medium">
                {fieldLabels[key] || key}
              </p>
              <p className="text-gray-800 mt-1">
                {Array.isArray(value) ? (
                  <ul className="list-disc list-inside">
                    {value.map((item, idx) => (
                      <li key={idx} className="text-sm">{formatValue(item)}</li>
                    ))}
                  </ul>
                ) : typeof value === 'object' ? (
                  <pre className="text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                    {formatValue(value)}
                  </pre>
                ) : (
                  <span className="font-semibold">{formatValue(value)}</span>
                )}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default StructuredFields;
