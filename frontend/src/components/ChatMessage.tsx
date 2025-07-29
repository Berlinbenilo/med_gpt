import React from 'react';
import { User, Bot, Zap } from 'lucide-react';
import { Message } from '../types/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isStreaming = false }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`flex gap-4 mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
          <Bot size={16} className="text-white" />
        </div>
      )}
      
      <div className={`max-w-[80%] ${isUser ? 'order-first' : ''}`}>
        <div
          className={`
            px-4 py-3 rounded-2xl text-sm leading-relaxed
            ${isUser 
              ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white ml-auto' 
              : 'bg-white text-gray-800 shadow-sm border border-gray-100'
            }
            transition-all duration-200 hover:shadow-md
            prose prose-sm max-w-none
            ${isUser ? 'prose-invert' : ''}
          `}
        >
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              // Override default elements with custom styling
              p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({children}) => <ul className="list-disc ml-4 mb-2">{children}</ul>,
              ol: ({children}) => <ol className="list-decimal ml-4 mb-2">{children}</ol>,
              h3: ({children}) => <h3 className="font-bold text-base mb-2">{children}</h3>,
              code: ({children}) => (
                <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">
                  {children}
                </code>
              ),
              pre: ({children}) => (
                <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto">
                  {children}
                </pre>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
          {isStreaming && message.content?.length === 0 && (
            <div className="flex items-center space-x-1">
                      <span className="dot animate-bounce">
                        <span className="flex w-2 h-2 bg-[#4f4f4f33] rounded-full"></span>
                      </span>
                      <span className="dot animate-bounce delay-100">
                        <span className="flex w-2 h-2 bg-[#4f4f4f33] rounded-full"></span>
                      </span>
                      <span className="dot animate-bounce delay-200">
                        <span className="flex w-2 h-2 bg-[#4f4f4f33] rounded-full"></span>
                      </span>
                    </div>
          )}
        </div>
        <div className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
      
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
          <User size={16} className="text-white" />
        </div>
      )}
    </div>
  );
};