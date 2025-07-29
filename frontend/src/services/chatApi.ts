const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://4.247.31.117:8000';
console.log("Loaded API URL:", import.meta.env.VITE_API_URL);

export interface ChatRequest {
  input_query: string;
  config: {
    model_name: string;
  };
  user_id?: string;
  session_id?: string;
}

export interface ChatResponse {
  message: string;
}

export interface Model {
  id: string;
  name: string;
  description?: string;
  owned_by?: string;
  created?: number;
}

export interface StreamChunk {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    delta: {
      role?: string;
      content?: string;
    };
    finish_reason: string | null;
  }>;
}

export class ChatApiService {
  private static instance: ChatApiService;
  private sessionId: string;

  constructor() {
    this.sessionId = this.generateSessionId();
  }

  static getInstance(): ChatApiService {
    if (!ChatApiService.instance) {
      ChatApiService.instance = new ChatApiService();
    }
    return ChatApiService.instance;
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async fetchModels(): Promise<Model[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/models`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data.data || data.models || [];
    } catch (error) {
      console.error('Fetch models error:', error);
      return [];
    }
  }

  async sendMessage(message: string, model: string): Promise<string> {
    try {
      const chatRequest: ChatRequest = {
        input_query: message,
        config: {
          model_name: model
        },
        user_id: "user_1",
        session_id: this.sessionId
      };

      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chatRequest),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ChatResponse = await response.json();
      return data.message;
    } catch (error) {
      console.error('Chat API error:', error);
      throw new Error('Failed to get response from chat service');
    }
  }

  async *sendMessageStream(message: string, model: string): AsyncGenerator<string, void, unknown> {
    try {
      const chatRequest: ChatRequest = {
        input_query: message,
        config: {
          model_name: model
        },
        user_id: "user_1",
        session_id: this.sessionId
      };

      console.log('Starting stream request...');
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chatRequest),
      });

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
                
                // Handle completion signal
                if (chunk.done) {
                  console.log('Stream done signal received');
                  return;
                }
                
                // Handle error
                if (chunk.error) {
                  throw new Error(chunk.error);
                }
                
                // Handle content
                if (chunk.content) {
                  yield chunk.content;
                }
              } catch (parseError) {
                console.warn('Failed to parse chunk:', data, parseError);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('Stream chat API error:', error);
      throw new Error('Failed to get streaming response from chat service');
    }
  }

  getSessionId(): string {
    return this.sessionId;
  }

  resetSession(): void {
    this.sessionId = this.generateSessionId();
  }
}
