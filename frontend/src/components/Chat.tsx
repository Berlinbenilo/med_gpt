import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { ChatHeader } from './ChatHeader';
import { TypingIndicator } from './TypingIndicator';
import { SessionSidebar } from './SessionSidebar';
import { Message, SessionWithMessages } from '../types/chat';
import { ChatApiService, Model } from '../services/chatApi';
import { SessionApiService } from '../services/sessionApi';

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hello! I'm MediTutor AI, your medical knowledge assistant. I can help you with medical questions, explain concepts, and provide educational information. How can I assist you today?",
      role: 'assistant',
      timestamp: new Date(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(true);
  const [model, setModel] = useState<string>("deepseek-r1-0528"); // Default model
  const [modelList, setModelList] = useState<Model[]>([]); // Model list
  const [isStreaming, setIsStreaming] = useState<boolean>(true); // Streaming mode
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState<string>('');
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatApiService = ChatApiService.getInstance();
  const sessionApiService = SessionApiService.getInstance();
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const models = await chatApiService.fetchModels();
        console.log("models", models);
        setModelList(models);
        if (models.length > 0 && !model) {
          setModel(models[0].id);
        }
      } catch (err) {
        console.error('Error fetching models:', err);
      }
    };

    fetchModels();
  }, [chatApiService]);

  // Effect to scroll when streaming message updates
  useEffect(() => {
    if (currentStreamingMessage) {
      scrollToBottom();
    }
  }, [currentStreamingMessage]);

  // Initialize with current session ID on mount
  useEffect(() => {
    setCurrentSessionId(chatApiService.getSessionId());
  }, []);

  const handleSendMessage = useCallback(async (content: string) => {
    // Cancel any ongoing streaming
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    setCurrentStreamingMessage('');
    setStreamingMessageId(null);

    if (isStreaming) {
      await handleStreamingResponse(content);
    } else {
      await handleStandardResponse(content);
    }
  }, [model, isStreaming]);

  const handleStandardResponse = async (content: string) => {
    try {
      const response = await chatApiService.sendMessage(content, model);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response,
        role: 'assistant',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsConnected(true);
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStreamingResponse = async (content: string) => {
    try {
      abortControllerRef.current = new AbortController();
      const messageId = (Date.now() + 1).toString();
      setStreamingMessageId(messageId);
      
      // Add empty assistant message that will be updated
      const assistantMessage: Message = {
        id: messageId,
        content: '',
        role: 'assistant',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      
      let fullContent = '';
      
      for await (const chunk of chatApiService.sendMessageStream(content, model)) {
        if (abortControllerRef.current?.signal.aborted) {
          break;
        }
        
        fullContent += chunk;
        setCurrentStreamingMessage(fullContent);
        
        // Update the message in the messages array
        setMessages(prev => 
          prev.map(msg => 
            msg.id === messageId 
              ? { ...msg, content: fullContent }
              : msg
          )
        );
      }
      
      setIsConnected(true);
    } catch (err) {
      handleError(err);
    } finally {
      setIsLoading(false);
      setCurrentStreamingMessage('');
      setStreamingMessageId(null);
      abortControllerRef.current = null;
    }
  };

  const handleError = (err: unknown) => {
    setError(err instanceof Error ? err.message : 'An error occurred');
    setIsConnected(false);
    
    // Add error message to chat
    const errorMessage: Message = {
      id: (Date.now() + 2).toString(),
      content: 'Sorry, I encountered an error processing your request. Please check your connection and try again.',
      role: 'assistant',
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, errorMessage]);
  };

  const fetchSession = async (sessionId: string) => {
    const session = await sessionApiService.getSessionWithMessages(sessionId);
    if (session) {
      setCurrentSessionId(sessionId);
      const loadedMessages: Message[] = session.messages.map((msg) => {
        return {
          id: msg.message_id,
          content: msg.content,
          role: msg.role,
          timestamp: new Date(msg.timestamp),
        };
      });
      setMessages(loadedMessages);
    }
  };

  const handleSessionSelect = (sessionId: string) => {
    fetchSession(sessionId);
    setIsSidebarOpen(false);
  };

  const handleNewChat = () => {
    setMessages([]);
    chatApiService.resetSession();
    setCurrentSessionId(chatApiService.getSessionId());
    setError(null);
    setCurrentStreamingMessage('');
    setStreamingMessageId(null);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Session Sidebar */}
      <SessionSidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewChat={handleNewChat}
      />
      
      {/* Main Chat Area */}
      <div className={`flex flex-col flex-1 transition-all duration-300 ${
        isSidebarOpen ? 'ml-0' : ''
      }`}>
        <ChatHeader 
          isConnected={isConnected}
          modelList={modelList}
          selectedModel={model}
          setModel={setModel}
          isStreaming={isStreaming}
          setIsStreaming={setIsStreaming}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        />
        
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto px-4 py-6">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <h3 className="text-lg font-medium mb-2">Hello! I'm MediTutor AI</h3>
                <p>Your medical knowledge assistant. How can I help you today?</p>
              </div>
            ) : (
              messages.map((message) => (
                <ChatMessage 
                  key={message.id} 
                  message={message} 
                  isStreaming={message.id === streamingMessageId}
                />
              ))
            )}
            
            {isLoading && !streamingMessageId && <TypingIndicator />}
            
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm flex justify-between items-center">
                <div>
                  <strong>Error:</strong> {error}
                </div>
                <button
                  onClick={() => setError(null)}
                  className="text-red-600 hover:text-red-800 font-medium text-sm"
                >
                  Dismiss
                </button>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>
        
        <div className="border-t border-gray-200 bg-white">
          <div className="max-w-4xl mx-auto">
            <ChatInput 
              onSendMessage={handleSendMessage} 
              disabled={isLoading} 
              onNewChat={handleNewChat}
              streamingMode={isStreaming}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
