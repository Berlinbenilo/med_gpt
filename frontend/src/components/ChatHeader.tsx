import React from 'react';
import { MessageCircle, Wifi, WifiOff, Zap, Settings } from 'lucide-react';
import { Model } from '../services/chatApi';

interface ChatHeaderProps {
  isConnected?: boolean;
  modelList?: Model[];
  selectedModel?: string;
  setModel?: (model: string) => void;
  isStreaming?: boolean;
  setIsStreaming?: (streaming: boolean) => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ 
  isConnected = true, 
  modelList, 
  selectedModel,
  setModel,
  isStreaming = true,
  setIsStreaming
}) => {
  const selectedModelData = modelList?.find(m => m.id === selectedModel);
  
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
            <MessageCircle size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-800">MediTutor AI</h1>
            <p className="text-sm text-gray-500">Medical Knowledge Assistant</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Model Selector */}
          <div className="flex flex-col">
            <label className="text-xs text-gray-500 mb-1">Model</label>
            <div className="relative">
              <select
                value={selectedModel || ''}
                className="bg-white border border-gray-300 rounded-lg px-3 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[200px]"
                onChange={(e) => setModel && setModel(e.target.value)}
              >
                {modelList?.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
              </select>
              <Settings size={14} className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none" />
            </div>
            {selectedModelData?.description && (
              <p className="text-xs text-gray-400 mt-1 max-w-[200px] truncate">
                {selectedModelData.description}
              </p>
            )}
          </div>

          {/* Streaming Toggle */}
          <div className="flex flex-col">
            <label className="text-xs text-gray-500 mb-1">Response Mode</label>
            <button
              onClick={() => setIsStreaming && setIsStreaming(!isStreaming)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isStreaming 
                  ? 'bg-blue-100 text-blue-700 border border-blue-200' 
                  : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
              }`}
            >
              <Zap size={14} className={isStreaming ? 'text-blue-600' : 'text-gray-500'} />
              {isStreaming ? 'Streaming' : 'Standard'}
            </button>
          </div>

          {/* Connection Status */}
          {isConnected ? (
            <div className="flex items-center gap-2 text-green-600">
              <Wifi size={16} />
              <span className="text-sm font-medium">Online</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-500">
              <WifiOff size={16} />
              <span className="text-sm font-medium">Offline</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
