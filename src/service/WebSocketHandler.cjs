const WebSocket = require('ws');

class WebSocketHandler {
    constructor() {
        this.clients = new Map();
    }

    initialize(server) {
        this.wss = new WebSocket.Server({
            noServer: true,
            maxPayload: 5 * 1024 * 1024,
            perMessageDeflate: false
        });

        this.setupHandlers();

        // Manejo de upgrade HTTP
        server.on('upgrade', (request, socket, head) => {
            if (request.url === '/video-socket') {
                this.wss.handleUpgrade(request, socket, head, (ws) => {
                    this.wss.emit('connection', ws);
                });
            }
        });
    }

    setupHandlers() {
        this.wss.on('connection', (ws) => {
            console.log('New WebSocket connection established');

            ws.isAlive = true;
            ws.on('pong', () => {
                ws.isAlive = true;
            });

            ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data);
                    this.handleMessage(ws, message);
                } catch (error) {
                    console.error('Error processing message:', error);
                    this.handleError(ws, error);
                }
            });

            ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                this.handleError(ws, error);
            });

            ws.on('close', () => {
                console.log('Client disconnected');
                this.clients.delete(ws);
            });
        });

        this.setupHeartbeat();
    }

    handleMessage(ws, message) {
        try {
            switch (message.type) {
                case 'register':
                    this.handleRegistration(ws, message);
                    break;
                case 'video-frame':
                    this.handleVideoFrame(ws, message);
                    break;
                default:
                    console.warn('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error in handleMessage:', error);
            this.handleError(ws, error);
        }
    }

    handleRegistration(ws, message) {
        this.clients.set(ws, {
            type: message.client,
            timestamp: Date.now()
        });
        console.log(`Client registered as ${message.client}`);

        // Enviar confirmación de registro
        this.sendSafe(ws, {
            type: 'registration_success',
            client: message.client
        });
    }

    handleVideoFrame(ws, message) {
        const clientInfo = this.clients.get(ws);
        if (!clientInfo || clientInfo.type !== 'web') {
            return;
        }

        this.clients.forEach((info, client) => {
            if (client !== ws &&
                info.type === 'python' &&
                client.readyState === WebSocket.OPEN) {
                this.sendSafe(client, {
                    type: 'video',
                    frame: message.frame
                });
            }
        });
    }

    sendSafe(ws, data) {
        try {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(data));
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.handleError(ws, error);
        }
    }

    handleError(ws, error) {
        console.error('WebSocket error occurred:', error);
        try {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close(1011, 'Internal server error');
            }
        } catch (closeError) {
            console.error('Error closing connection:', closeError);
        }
    }

    setupHeartbeat() {
        const interval = setInterval(() => {
            this.wss.clients.forEach((ws) => {
                if (ws.isAlive === false) {
                    this.clients.delete(ws);
                    return ws.terminate();
                }

                ws.isAlive = false;
                ws.ping(() => { });
            });
        }, 30000);

        this.wss.on('close', () => {
            clearInterval(interval);
        });
    }
}

module.exports = new WebSocketHandler();