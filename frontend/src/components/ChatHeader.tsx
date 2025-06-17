import React from 'react';
import { MessageCircle, Wifi, WifiOff } from 'lucide-react';

interface ChatHeaderProps {
  isConnected?: boolean;
  modelList?: [{ id: string; name: string }];
  setModel?: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({ isConnected = true, modelList, setModel }) => {
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
            <MessageCircle size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-800">MediTutor</h1>
            <p className="text-sm text-gray-500">Science & Knowledge</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="relative">
            <select
              className="bg-white border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              onChange={(e) => setModel && setModel(e.target.value)}
            >
              {modelList?.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
            </div>
          {isConnected ? (
            <div className="flex items-center gap-2 text-green-600">
              <Wifi size={16} />
              <span className="text-sm font-medium">Connected</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-500">
              <WifiOff size={16} />
              <span className="text-sm font-medium">Disconnected</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};