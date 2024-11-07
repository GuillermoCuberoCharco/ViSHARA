import io from 'socket.io-client';

class SocketService {
    constructor() {
        this.messageSocket = null;
        this.videoSocket = null;
        this.messageListeners = new Map();
        this.connectionListeners = new Map();
        this.isRegistered = false;
    }

    async connectMessageSocket() {
        try {
            const socket = io("ws://localhost:8081/messages", {
                transports: ['polling', 'websocket'],
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionAttempts: 5
            });

            return new Promise((resolve, reject) => {
                socket.on('connect', () => {
                    this.messageSocket = socket;
                    this.setupMessageSocketListeners();
                    socket.emit('register_client', 'web');
                });

                socket.on('registration_success', () => {
                    this.isRegistered = true;
                    resolve(socket);
                });

                socket.on('registration_error', (error) => {
                    reject(new Error(error.message));
                });

                socket.onº('connect_error', (error) => {
                    reject(error);
                });

            });
        } catch (error) {
            console.error('Error connecting to message socket:', error);
            throw error;
        }
    }

    setupMessageSocketListeners() {
        if (!this.messageSocket) return;

        this.messageSocket.on('watson_message', (message) => {
            this.notifyListeners('watson_message', message);
        });

        this.messageSocket.on('wizard_message', (message) => {
            this.notifyListeners('wizard_message', message);
        });

        this.messageSocket.on('client_message', (message) => {
            this.notifyListeners('client_message', message);
        });

        this.messageSocket.on('disconnect', () => {
            this.isRegistered = false;
            this.notifyListeners('connection', { status: 'disconnected' });
        });
    }

    connectVideoSocket() {
        try {
            this.videoSocket = new WebSocket('ws://localhost:8081/video-socket');

            this.videoSocket.onopen = () => {
                this.videoSocket.send(JSON.stringify({ type: 'register', client: 'web' }));
                this.notifyListeners('connection', { status: 'video_connected' });
            };

            this.videoSocket.onerror = (error) => {
                console.error('Video socket error:', error);
                this.notifyListeners('connection', { status: 'video_error', error });
                setTimeout(() => this.connectVideoSocket(), 5000);
            };

            this.videoSocket.onclose = () => {
                this.notifyListeners('connection', { status: 'video_disconnected' });
                setTimeout(() => this.connectVideoSocket(), 5000);
            };
        } catch (error) {
            console.error('Error connecting to video socket:', error);
            setTimeout(() => this.connectVideoSocket(), 5000);
        }
    }

    sendMessage(message) {
        if (!this.messageSocket || !this.isRegistered) {
            throw new Error('Message socket is not connected or registered');
        }

        this.messageSocket.emit('message', message);
    }

    sendVideoFrame(frame) {
        if (this.videoSocket?.readyState === WebSocket.OPEN) {
            this.videoSocket.send(JSON.stringify({ type: 'video_frame', frame }));
        }
    }

    addListener(event, callback) {
        if (!this.messageListeners.has(event)) {
            this.messageListeners.set(event, new Set());
        }

        this.messageListeners.get(event).push(callback);
    }

    removeListener(event, callback) {
        const listeners = this.messageListeners.get(event);
        if (listeners) {
            listeners.delete(callback);
        }
    }

    notifyListeners(event, data) {
        const listeners = this.messageListeners.get(event);
        if (listeners) {
            listeners.forEach((callback) => callback(data));
        }
    }

    disconnect() {
        if (this.messageSocket) {
            this.messageSocket.disconnect();
        }
        if (this.videoSocket) {
            this.videoSocket.disconnect();
        }
    }
}

export const socketService = new SocketService();