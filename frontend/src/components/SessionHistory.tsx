import React, { useEffect, useState } from 'react';
import { ChatSession } from '../types/chat';
import { SessionApiService } from '../services/sessionApi';

export const SessionHistory: React.FC = () => {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const sessionApiService = SessionApiService.getInstance();

    useEffect(() => {
        const fetchSessions = async () => {
            const userSessions = await sessionApiService.getUserSessions();
            setSessions(userSessions);
        };

        fetchSessions();
    }, []);

    if (!sessions.length) {
        return <div>No sessions found.</div>;
    }

    return (
        <div>
            <h2>Session History</h2>
            <ul>
                {sessions.map((session) => (
                    <li key={session.session_id}>
                        <strong>{session.title}</strong> - {session.message_count} messages
                    </li>
                ))}
            </ul>
        </div>
    );
};

