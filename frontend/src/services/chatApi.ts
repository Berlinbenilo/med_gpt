const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://4.247.31.117:8000';
console.log("Loaded API URL:", import.meta.env.VITE_API_URL);

export interface ChatRequest {
  input_query: string;
  config: {
    model_name: string;
  };
}

export interface ChatResponse {
  message: string;
}

export class ChatApiService {
  private static instance: ChatApiService;

  static getInstance(): ChatApiService {
    if (!ChatApiService.instance) {
      ChatApiService.instance = new ChatApiService();
    }
    return ChatApiService.instance;
  }

  async fetchModels(): Promise<Array<{ id: string; name: string }>> {
    try {
      const response = await fetch(`${API_BASE_URL}/models`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Fetch models error:', error);
      return [];
    }
  }

  async sendMessage(message: string, model:string): Promise<string> {
    try {
      const chatRequest: ChatRequest = {
        input_query: message,
        config: {
          model_name: model
        }
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
      return data.message; // Changed from data.response to data.message
    } catch (error) {
      console.error('Chat API error:', error);
      throw new Error('Failed to get response from chat service');
    }
  }
}