const EventEmitter = require('events');

class ClientManager extends EventEmitter {
    constructor() {
        super();
        this.clients = new Map();
        this.types = new Set(['web', 'python']);
    }

    addClient(socket, type) {
        if (!this.types.has(type)) {
            throw new Error(`Invalid client type: ${type}`);
        }

        const clientInfo = {
            socket,
            type,
            connectedAt: Date(),
            lastActivity: Date()
        };

        this.clients.set(socket.id, clientInfo);
        this.emit('clientAdded', { socketId: socket.id, type });

        return clientInfo;
    }

    removeClient(socketId) {
        const client = this.clients.get(socketId);
        if (client) {
            this.clients.delete(socketId);
            this.emit('clientRemoved', { socketId, type: client.type });
        }
        return client;
    }

    getClient(socketId) {
        return this.clients.get(socketId);
    }

    getClientsByType(type) {
        return Array.from(this.clients.values()).filter(client => client.type === type);
    }

    updateClientActivity(socketId) {
        const client = this.clients.get(socketId);
        if (client) {
            client.lastActivity = Date();
        }
    }

    isValidClient(socketId, type) {
        const client = this.clients.get(socketId);
        return client && client.type === type;
    }

    boradcast(message, excludeSocketId = null) {
        this.clients.forEach((client, socketId) => {
            if (socketId !== excludeSocketId && client.socket.connected) {
                client.socket.emit('message', message);
            }
        });
    }

    boradcastToType(type, message, excludeSocketId = null) {
        this.getClientsByType(type).forEach(client => {
            if (client.socket.id !== excludeSocketId && client.socket.connected) {
                client.socket.emit('message', message);
            }
        });
    }
}

module.exports = ClientManager;