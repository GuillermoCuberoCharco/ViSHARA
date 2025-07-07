const webClients = new Map();
const operatorCLients = new Map();
const sessionClients = new Map();

/**
 * Registers a client in the system.
 */
function registerClient(socketId, socket, clientData) {
    const { type = 'participant', sessionId = 'default' } = clientData;

    const clientInfo = { socket, sessionId, type, socketId };

    if (type === 'operator') {
        operatorCLients.set(socketId, clientInfo);
    } else {
        webClients.set(socketId, clientInfo);
    }

    if (!sessionClients.has(sessionId)) {
        sessionClients.set(sessionId, new Set());
    }
    sessionClients.get(sessionId).add(socketId);

    console.log(`Client registered: ${type} in session ${sessionId}`);
    return clientInfo;
}

/**
 * Unregisters a client from the system.
 */
function unregisterClient(socketId) {
    const webClient = webClients.get(socketId);
    const operatorClient = operatorCLients.get(socketId);
    const client = webClient || operatorClient;

    if (client) {
        const { sessionId } = client;

        webClients.delete(socketId);
        operatorCLients.delete(socketId);

        if (sessionClients.has(sessionId)) {
            sessionClients.get(sessionId).delete(socketId);
            if (sessionClients.get(sessionId).size === 0) {
                sessionClients.delete(sessionId);
            }
        }
        console.log(`Client unregistered: ${client.type} in session ${sessionId}`);
        return client;
    }
}

/**
 * Broadcasts a message to all clients in a session.
 */
function broadcastToSession(sessionId, event, data, excludeSocketId = null) {
    const sessionSockets = sessionClients.get(sessionId);
    if (!sessionSockets) return 0;

    let broadcastCount = 0;

    sessionSockets.forEach(socketId => {
        if (socketId === excludeSocketId) return;

        const webClient = webClients.get(socketId);
        const operatorClient = operatorCLients.get(socketId);
        const client = webClient || operatorClient;

        if (client && client.socket && client.socket.connected) {
            try {
                client.socket.emit(event, data);
                broadcastCount++;
            } catch (error) {
                console.error(`Error broadcasting to ${client.type} client ${socketId}:`, error);
            }
        }
    });
    console.log(`Broadcasted ${event} to ${broadcastCount} clients in session ${sessionId}`);
    return broadcastCount;
}

/**
 * Gets a iformation about a client by its socket ID.
 */
function getClientInfo(socketId) {
    return webClients.get(socketId) || operatorCLients.get(socketId) || null;
}

/**
 * Gets all clients in a session.
 */
function getClientsInSession(sessionId) {
    const socketIds = sessionClients.get(sessionId);
    if (!socketIds) return [];

    const clients = [];
    socketIds.forEach(socketId => {
        const client = getClientInfo(socketId);
        if (client) clients.push(client);
    });
    return clients;
}

/**
 * Gets system statistics.
 */
function getStats() {
    return {
        totalClients: webClients.size + operatorCLients.size,
        webClients: webClients.size,
        operatorClients: operatorCLients.size,
        activeSessions: sessionClients.size,
        sessionDetails: Array.from(sessionClients.entries()).map(([sessionId, sockets]) => ({
            sessionId,
            clientCount: sockets.size
        }))
    };
}

module.exports = {
    registerClient,
    unregisterClient,
    broadcastToSession,
    getClientInfo,
    getClientsInSession,
    getStats
};