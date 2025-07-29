import React from 'react';
import { Bot } from 'lucide-react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex gap-4 mb-6 justify-start">
      <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
        <Bot size={16} className="text-white" />
      </div>
      
      <div className="bg-white text-gray-800 shadow-sm border border-gray-100 px-4 py-3 rounded-2xl">
        <div className="flex gap-1 items-center">
          <div className="w-2 h-2 bg-[#4f4f4f33] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-[#4f4f4f33] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-[#4f4f4f33] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  );
};