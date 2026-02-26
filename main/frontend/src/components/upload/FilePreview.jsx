// frontend/src/components/upload/FilePreview.jsx
// Shows selected file info before submitting

export default function FilePreview({ file, onRemove }) {
  if (!file) return null;

  const sizeKB = (file.size / 1024).toFixed(1);
  const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
  const displaySize = file.size > 1024 * 1024 ? `${sizeMB} MB` : `${sizeKB} KB`;

  const isImage = file.type.startsWith("image/");
  const isPDF   = file.type === "application/pdf";

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg mt-3">
      <div className="flex items-center gap-3">
        {/* Icon */}
        <div className="text-2xl">
          {isPDF ? "📄" : isImage ? "🖼️" : "📁"}
        </div>

        {/* File info */}
        <div>
          <p className="text-sm font-medium text-gray-800 truncate max-w-xs">
            {file.name}
          </p>
          <p className="text-xs text-gray-500">
            {displaySize} · {file.type || "unknown type"}
          </p>
        </div>
      </div>

      {/* Remove button */}
      <button
        onClick={onRemove}
        className="text-gray-400 hover:text-red-500 transition-colors text-lg leading-none"
        title="Remove file"
      >
        ✕
      </button>
    </div>
  );
}
