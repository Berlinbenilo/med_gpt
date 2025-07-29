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

// Session-related types
export interface ChatSession {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface SessionWithMessages extends ChatSession {
  user_id: string;
  model_config: any;
  messages: SessionMessage[];
}

export interface SessionMessage {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  node_type?: string;
  metadata?: any;
}

export interface SessionsResponse {
  sessions: ChatSession[];
}

