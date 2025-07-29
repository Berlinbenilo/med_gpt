import React, { useState, useEffect } from 'react';
import { ChatSession } from '../types/chat';
import { SessionApiService } from '../services/sessionApi';

interface SessionSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  currentSessionId: string;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({
  isOpen,
  onToggle,
  currentSessionId,
  onSessionSelect,
  onNewChat,
}) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingSession, setEditingSession] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const sessionApiService = SessionApiService.getInstance();

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const userSessions = await sessionApiService.getUserSessions();
      setSessions(userSessions);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    } finally {
      setLoading(false);
    }
  };
console.log("isopen",isOpen)
  useEffect(() => {
    if (isOpen) {
      fetchSessions();
    }
  }, [isOpen]);

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this conversation?')) {
      const success = await sessionApiService.deleteSession(sessionId);
      if (success) {
        setSessions(prev => prev.filter(s => s.session_id !== sessionId));
        if (sessionId === currentSessionId) {
          onNewChat();
        }
      }
    }
  };

  const handleEditTitle = async (sessionId: string) => {
    if (editTitle.trim() && editTitle !== sessions.find(s => s.session_id === sessionId)?.title) {
      const success = await sessionApiService.updateSessionTitle(sessionId, editTitle.trim());
      if (success) {
        setSessions(prev =>
          prev.map(s =>
            s.session_id === sessionId ? { ...s, title: editTitle.trim() } : s
          )
        );
      }
    }
    setEditingSession(null);
    setEditTitle('');
  };

  const startEdit = (session: ChatSession, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSession(session.session_id);
    setEditTitle(session.title);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  // Group sessions by date
  const groupedSessions = sessions.reduce((groups: Record<string, ChatSession[]>, session) => {
    const dateKey = formatDate(session.created_at);
    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(session);
    return groups;
  }, {});

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed left-0 top-0 h-full bg-gray-900 text-white transform transition-transform duration-300 ease-in-out z-50 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } w-80`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <h2 className="text-lg font-semibold">Chat History</h2>
            <button
              onClick={onToggle}
              className="p-1 rounded hover:bg-gray-700 "
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* New Chat Button */}
          <div className="p-4">
            <button
              onClick={() => {
                onNewChat();
                onToggle();
              }}
              className="w-full flex items-center gap-3 p-3 rounded-lg border border-gray-600 hover:bg-gray-800 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New chat
            </button>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto px-4 pb-4">
            {loading ? (
              <div className="text-center text-gray-400 py-8">Loading sessions...</div>
            ) : sessions.length === 0 ? (
              <div className="text-center text-gray-400 py-8">No conversations yet</div>
            ) : (
              Object.entries(groupedSessions).map(([dateGroup, groupSessions]) => (
                <div key={dateGroup} className="mb-6">
                  <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
                    {dateGroup}
                  </h3>
                  <div className="space-y-1">
                    {groupSessions.map((session) => (
                      <div
                        key={session.session_id}
                        className={`group flex items-center gap-2 p-2 rounded-lg cursor-pointer hover:bg-gray-800 transition-colors ${
                          currentSessionId === session.session_id ? 'bg-gray-800' : ''
                        }`}
                        onClick={() => {
                          onSessionSelect(session.session_id);
                          onToggle();
                        }}
                      >
                        <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.955 8.955 0 01-2.863-.476c-.198-.088-.485-.158-.67-.122l-3.825.784c-.518.106-.954-.328-.848-.846l.784-3.825c.036-.185-.034-.472-.122-.67A8.955 8.955 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z" />
                        </svg>
                        
                        {editingSession === session.session_id ? (
                          <input
                            type="text"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onBlur={() => handleEditTitle(session.session_id)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                handleEditTitle(session.session_id);
                              } else if (e.key === 'Escape') {
                                setEditingSession(null);
                                setEditTitle('');
                              }
                            }}
                            className="flex-1 bg-gray-700 text-white px-2 py-1 rounded text-sm"
                            autoFocus
                            onClick={(e) => e.stopPropagation()}
                          />
                        ) : (
                          <span className="flex-1 truncate text-sm">
                            {session.title}
                          </span>
                        )}

                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => startEdit(session, e)}
                            className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-white"
                            title="Edit title"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          <button
                            onClick={(e) => handleDeleteSession(session.session_id, e)}
                            className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-red-400"
                            title="Delete conversation"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
};
