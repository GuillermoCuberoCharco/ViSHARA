const fs = require('fs');
const path = require('path');

const DB_DIR = path.join(__dirname, '..', 'data');
const CONVERSATIONS_FILE = path.join(DB_DIR, 'conversations.json');

const MAX_MESSAGES_PER_SESSION = 100;
const MAX_SESSIONS_PER_USER = 10;
const MAX_CONTENT_MESSAGES = 100;

const conversationDatabase = {
    users: {}
};

async function initConversationService() {
    try {
        await fs.promises.mkdir(DB_DIR, { recursive: true });
        await loadConversationsFromFile();
        console.log('Conversation database initialized.');
    } catch (error) {
        console.error('Error initializing conversation database:', error);
    }
}

async function loadConversationsFromFile() {
    try {
        const data = await fs.promises.readFile(CONVERSATIONS_FILE, 'utf8');
        const loadedData = JSON.parse(data);
        conversationDatabase.users = loadedData.users || {};
        console.log(`Conversations loaded: ${Object.keys(conversationDatabase.users).length} users with conversations history.`);
    } catch (error) {
        if (error.code !== 'ENOENT') {
            console.error('Error loading conversations from file:', error);
        } else {
            console.log('No conversations file found. Starting with an empty database.');
            await saveConversationsToFile();
        }
    }
}

async function saveConversationsToFile() {
    try {
        await fs.promises.mkdir(DB_DIR, { recursive: true });
        await fs.promises.writeFile(CONVERSATIONS_FILE, JSON.stringify(conversationDatabase, null, 2), 'utf8');
    } catch (error) {
        console.error('Error saving conversations to file:', error);
    }
}

function startNewSession(userId) {
    if (!conversationDatabase.users[userId]) {
        conversationDatabase.users[userId] = {
            sessions: [],
            currentSession: null
        };
    }

    const newSession = {
        sessionId: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        startedAt: new Date().toISOString(),
        messages: [],
        isActive: true
    };

    if (conversationDatabase.users[userId].currentSession) {
        const currentSessionId = conversationDatabase.users[userId].currentSession;
        const currentSession = conversationDatabase.users[userId].sessions.find(s => s.sessionId === currentSessionId);
        if (currentSession) {
            currentSession.isActive = false;
            currentSession.endedAt = new Date().toISOString();
        }
    }

    conversationDatabase.users[userId].sessions.push(newSession);
    conversationDatabase.users[userId].currentSession = newSession.sessionId;
    if (conversationDatabase.users[userId].sessions.length > MAX_SESSIONS_PER_USER) {
        conversationDatabase.users[userId].sessions = conversationDatabase.users[userId].sessions
            .slice(-MAX_SESSIONS_PER_USER);
    }

    console.log(`New conversation session started for user ${userId}: ${newSession.sessionId}`);
    return newSession.sessionId;
}

async function addMessage(userId, role, content, metadata = {}) {
    try {
        if (!conversationDatabase.users[userId]) startNewSession(userId);

        const currentSessionId = conversationDatabase.users[userId].currentSession;

        if (!currentSessionId) startNewSession(userId);

        const session = conversationDatabase.users[userId].sessions.find(session => session.sessionId === currentSessionId);

        if (!session) return false;

        const message = {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            role: role,
            content: content.trim(),
            timestamp: new Date().toISOString(),
            metadata: metadata
        }

        session.messages.push(message);

        if (session.messages.length > MAX_MESSAGES_PER_SESSION) {
            session.messages = session.messages.slice(-MAX_MESSAGES_PER_SESSION);
        }

        if (session.messages.length % 5 === 0) {
            await saveConversationsToFile();
        }

        console.log(`Message added to session ${currentSessionId} for user ${userId}: ${message.id}`);
        return true;
    } catch (error) {
        console.error('Error adding message:', error);
        return false;
    }
}

function getConversationContext(userId, maxMessages = MAX_CONTENT_MESSAGES) {
    try {
        if (!conversationDatabase.users[userId]) return [];

        const allSessions = conversationDatabase.users[userId].sessions.sort((a, b) => new Date(b.startedAt) - new Date(a.startedAt));

        const contextMessages = [];

        for (const session of allSessions) {
            const sessionMessages = session.messages
                .filter(msg => msg.content && msg.content.trim() !== '')
                .map(msg => ({
                    role: msg.role === 'assistant' || msg.role === 'wizard' ? 'assistant' : 'user',
                    content: msg.content,
                    timestamp: msg.timestamp
                }));

            contextMessages.unshift(...sessionMessages);
            if (contextMessages.length >= maxMessages) break;
        }
        const finalContext = contextMessages.slice(-maxMessages);
        console.log(`Conversation context for user ${userId} retrieved: ${finalContext.length} messages`);
        return finalContext;
    } catch (error) {
        console.error('Error getting conversation context:', error);
        return [];
    }
}

function getUserConversationHistory(userId) {
    if (!conversationDatabase.users[userId]) {
        return {
            totalSessions: 0,
            totalMessages: 0,
            firstConversation: null,
            lastConversation: null,
            currentSessionActive: false
        };
    }

    const user = conversationDatabase.users[userId];
    const totalMessages = user.sessions.reduce((total, session) => total + session.messages.length, 0);

    const sortedSessions = user.sessions.sort((a, b) => new Date(a.startedAt) - new Date(b.startedAt));

    return {
        totalSessions: sortedSessions.length,
        totalMessages: totalMessages,
        firstConversation: sortedSessions.length > 0 ? sortedSessions[0].startedAt : null,
        lastConversation: sortedSessions.length > 0 ? sortedSessions[sortedSessions.length - 1].startedAt : null,
        currentSessionActive: user.currentSession !== null
    };
}

async function endCurrentSession(userId) {
    try {
        if (!conversationDatabase.users[userId] || !conversationDatabase.users[userId].currentSession) return false;

        const currentSessionId = conversationDatabase.users[userId].currentSession;
        const session = conversationDatabase.users[userId].sessions.find(s => s.sessionId === currentSessionId);

        if (session) {
            session.isActive = false;
            session.endedAt = new Date().toISOString();
            conversationDatabase.users[userId].currentSession = null;

            await saveConversationsToFile();
            console.log(`Session ended for user ${userId}: ${currentSessionId}`);
            return true;
        }

        return false;
    } catch (error) {
        console.error('Error ending session:', error);
        return false;
    }
}

async function cleanupOldConversations(daysOld = 90) {
    try {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - daysOld);

        let totalCleaned = 0;

        for (const userId in conversationDatabase.users) {
            const user = conversationDatabase.users[userId];
            const originalCount = user.sessions.length;

            user.sessions = user.sessions.filter(session => new Date(session.startedAt) > cutoffDate);

            const cleanedCount = originalCount - user.sessions.length;
            totalCleaned += cleanedCount;

            if (user.sessions.length === 0) delete conversationDatabase.users[userId];
        }

        if (totalCleaned > 0) {
            await saveConversationsToFile();
            console.log(`Cleaned up ${totalCleaned} old conversation sessions older than ${daysOld} days`);
        }

        return totalCleaned;
    } catch (error) {
        console.log('Error cleaning up conversations:', error);
        return 0;
    }
}

function getConversationStats() {
    const stats = {
        totalUsers: Object.keys(conversationDatabase.users).length,
        totalSessions: 0,
        totalMessages: 0,
        activeSessions: 0,
        users: {}
    };

    for (const userId in conversationDatabase.users) {
        const userStats = getUserConversationHistory(userId);

        stats.totalSessions += userStats.totalSessions;
        stats.totalMessages += userStats.totalMessages;

        if (userStats.currentSessionActive) stats.activeSessions++;

        stats.users[userId] = userStats
    }

    return stats;
}

module.exports = {
    initConversationService,
    startNewSession,
    addMessage,
    getConversationContext,
    getUserConversationHistory,
    endCurrentSession,
    cleanupOldConversations,
    getConversationStats,
    saveConversationsToFile
};