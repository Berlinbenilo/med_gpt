import { ChatSession, SessionWithMessages, SessionsResponse } from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://4.247.31.117:8000';

export class SessionApiService {
  private static instance: SessionApiService;
  private userId: string = 'user_1'; // Default user ID

  static getInstance(): SessionApiService {
    if (!SessionApiService.instance) {
      SessionApiService.instance = new SessionApiService();
    }
    return SessionApiService.instance;
  }

  /**
   * Get all sessions for the current user
   */
  async getUserSessions(): Promise<ChatSession[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${this.userId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: SessionsResponse = await response.json();
      return data.sessions;
    } catch (error) {
      console.error('Error fetching user sessions:', error);
      return [];
    }
  }

  /**
   * Get a specific session with all its messages
   */
  async getSessionWithMessages(sessionId: string): Promise<SessionWithMessages | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${this.userId}/${sessionId}`);
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching session with messages:', error);
      return null;
    }
  }

  /**
   * Delete a session
   */
  async deleteSession(sessionId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${this.userId}/${sessionId}`, {
        method: 'DELETE',
      });
      return response.ok;
    } catch (error) {
      console.error('Error deleting session:', error);
      return false;
    }
  }

  /**
   * Update session title
   */
  async updateSessionTitle(sessionId: string, title: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${this.userId}/${sessionId}/title`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });
      return response.ok;
    } catch (error) {
      console.error('Error updating session title:', error);
      return false;
    }
  }

  /**
   * Set user ID (useful for multi-user support)
   */
  setUserId(userId: string): void {
    this.userId = userId;
  }

  /**
   * Get current user ID
   */
  getUserId(): string {
    return this.userId;
  }
}
