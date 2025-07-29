import React, { useState, useRef } from 'react';
import { Send, Plus } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  onNewChat?: () => void;
  streamingMode?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  disabled = false, 
  onNewChat,
  streamingMode = false 
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <form onSubmit={handleSubmit} className="flex gap-3 items-end">
        {onNewChat && (
          <button
            type="button"
            onClick={onNewChat}
            className="
              flex-shrink-0 w-12 h-12 bg-gray-100 hover:bg-gray-200 
              text-gray-600 rounded-2xl flex items-center justify-center
              transition-all duration-200 hover:shadow-lg hover:scale-105 active:scale-95
            "
            title="New Chat"
          >
            <Plus size={18} />
          </button>
        )}
        
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            disabled={disabled}
            className="
              w-full px-4 py-3 pr-12 rounded-2xl border border-gray-200 
              resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
              disabled:bg-gray-50 disabled:text-gray-400
              min-h-[52px] max-h-32 leading-6
              transition-all duration-200
            "
            rows={1}
          />
        </div>
        
        <button
          type="submit"
          disabled={!message.trim() || disabled}
          className="
            flex-shrink-0 w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 
            text-white rounded-2xl flex items-center justify-center
            hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
            transition-all duration-200 hover:shadow-lg hover:scale-105 active:scale-95
          "
        >
          <Send size={18} />
        </button>
      </form>
      
      <div className="flex justify-between items-center mt-2">
        <div className="text-xs text-gray-500">
          Press Enter to send, Shift+Enter for new line
        </div>
        {streamingMode && (
          <div className="text-xs text-blue-500 font-medium">
            Streaming mode active
          </div>
        )}
      </div>
    </div>
  );
};