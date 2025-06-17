export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export interface Model {
  id: string;
  name: string;
  description?: string;
}

export interface ModelsResponse {
  models: Model[];
}

// types/chat.ts
export interface ChatConfig {
  model_name: string;
  // add other config properties as needed
}

export interface ChatRequest {
  input_query: string;
  config: ChatConfig;
}


