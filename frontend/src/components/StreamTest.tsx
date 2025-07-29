import React, { useState } from 'react';

export const StreamTest: React.FC = () => {
  const [streamContent, setStreamContent] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);

  const testStreaming = async () => {
    setStreamContent('');
    setIsStreaming(true);
    
    try {
      const response = await fetch('http://4.247.31.117:8000/test/stream');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Failed to get response reader');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            console.log('Stream completed');
            break;
          }
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim();
              
              if (!data) continue;
              
              try {
                const chunk = JSON.parse(data);
                console.log('Received chunk:', chunk);
                
                if (chunk.done) {
                  console.log('Stream done signal received');
                  setIsStreaming(false);
                  return;
                }
                
                if (chunk.content) {
                  setStreamContent(prev => prev + chunk.content);
                }
              } catch (parseError) {
                console.warn('Failed to parse chunk:', data, parseError);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
        setIsStreaming(false);
      }
    } catch (error) {
      console.error('Stream test error:', error);
      setIsStreaming(false);
    }
  };

  return (
    <div className="p-4 border rounded-lg bg-gray-50">
      <h3 className="text-lg font-semibold mb-4">Stream Test</h3>
      
      <button
        onClick={testStreaming}
        disabled={isStreaming}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
      >
        {isStreaming ? 'Streaming...' : 'Test Stream'}
      </button>
      
      <div className="mt-4 p-3 bg-white border rounded">
        <h4 className="font-medium mb-2">Stream Output:</h4>
        <div className="whitespace-pre-wrap">{streamContent || 'No content yet...'}</div>
      </div>
    </div>
  );
};
