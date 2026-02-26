function MessageBubble({ message }) {
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const isUser = message.role === 'user';
  const isError = message.isError;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[70%] rounded-lg p-4 ${
        isUser 
          ? 'bg-blue-600 text-white' 
          : isError
          ? 'bg-red-50 text-red-800 border border-red-200'
          : 'bg-gray-100 text-gray-800'
      }`}>
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        <div className={`text-xs mt-2 ${
          isUser ? 'text-blue-100' : 'text-gray-500'
        }`}>
          {formatTime(message.timestamp)}
          {message.processingTime && (
            <span className="ml-2">• {message.processingTime}ms</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;
