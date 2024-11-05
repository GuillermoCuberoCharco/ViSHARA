const express = require('express');
const cors = require('cors');
const { Server } = require('socket.io');
const bodyParser = require('body-parser');
const WebSocketHandler = require('./WebSocketHandler.cjs');
const synthesize = require('./googleTTS.cjs');
const transcribe = require('./googleSTT.cjs');
const watsonService = require('./ibmWatsonService.cjs');
const faceTracker = require('./faceTracker.cjs');
const ClientManager = require('./ClientManager.cjs');
const http = require('http');
const { stat } = require('fs');

class ApplicationServer {
    constructor() {
        this.setupExpress();
        this.setupServer();
        this.setupSocketIO();
        this.setupWebSocket();
        this.setupServices();
        this.setupFaceDetection();

        this.clientManager = new ClientManager();
    }

    setupExpress() {
        this.app = express();
        this.app.use(cors({
            origin: true,
            methods: ['GET', 'POST'],
            credentials: true
        }));
        this.app.use(bodyParser.json({ limit: '5mb' }));
        this.app.use(bodyParser.urlencoded({ extended: true, limit: '5mb' }));

        // API routes
        this.app.post("/synthesize", synthesize);
        this.app.post('/transcribe', transcribe);
    }

    setupServer() {
        this.server = http.createServer(this.app);
    }

    setupSocketIO() {
        this.io = new Server(this.server, {
            cors: {
                origin: 'http://localhost:5173',
                methods: ['GET', 'POST'],
                credentials: true
            },
            transports: ['polling', 'websocket'],
        });

        // Namespace for general messages
        this.messageIo = this.io.of('/messages');
        this.setupMessageHandlers();
    }

    setupWebSocket() {
        WebSocketHandler.initialize(this.server);
    }

    // External services
    setupServices() {
        watsonService.createSession().catch(console.error);
    }

    setupFaceDetection() {
        faceTracker.setupRoutes(this.app);

        setInterval(() => {
            faceTracker.cleanupOldImages();
        }, 60 * 60 * 1000);
    }

    setupMessageHandlers() {
        this.messageIo.on('connection', (socket) => {
            console.log('New client connected to message namespace');

            socket.on('register_client', (clientType) => {
                try {
                    this.clientManager.addClient(socket, clientType);
                    socket.emit('registration_success', { type: clientType });
                    console.log(`Client registered as ${clientType}`);
                } catch (error) {
                    console.error(error);
                    socket.emit('registration_error', { error: error.message });
                }
            });

            socket.on('message', async (message) => {
                try {
                    const parsedMessage = typeof message === 'string' ? JSON.parse(message) : message;

                    this.clientManager.updateClientActivity(socket.id);

                    switch (parsedMessage.type) {
                        case 'client_message':
                            await this.handleClientMessage(socket, parsedMessage);
                            break;
                        case 'wizard_message':
                            await this.handelWizardMessage(socket, parsedMessage);
                            break;
                        default:
                            console.error('Unknown message type:', parsedMessage.type);
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                    socket.emit('error', { message: 'Error processing message' });
                }
            });

            socket.on('disconnect', () => {
                this.clientManager.removeClient(socket.id);
                console.log(`Client disconnected: ${socket.id}`);
            });
        });
    }
    async handleClientMessage(socket, message) {
        // this.clientManager.boradcastToType('python', {
        //     type: 'client_message',
        //     text: message.text,
        //     state: message.state
        // });

        try {
            const { response, userDefined, emotions, strongEmotion } = await watsonService.getWatsonResponse(message.text);

            const watsonText = response.output.generic[0].text;

            this.clientManager.boradcastToType('web', {
                type: 'watson_message',
                text: watsonText,
                emotions: emotions,
                state: strongEmotion
            });

            this.messageIo.emit('client_message', {
                text: message.text,
                state: message.state
            });

        } catch (error) {
            console.error('Error processing client message:', error);
            socket.emit('error', { message: 'Error processing client message' });
        }
    }

    handleWizardMessage(socket, message) {
        if (!this.clientManager.isValidClient(socket.id, 'python')) {
            socket.emit('error', { message: 'Unauthorized wizard message' });
            return;
        }

        this.clientManager.boradcastToType('web', {
            type: 'wizard_message',
            text: message.text,
            state: message.state
        });
    }

    setupVideohandlers() {
        this.wss.on('connection', (ws) => {
            console.log('New client connected to video WebSocket');

            ws.on('message', (message) => {
                try {
                    const data = JSON.parse(message);

                    if (data.type === 'register') {
                        ws.clientType = data.client;
                        console.log(`Client registered as ${data.client}`);
                    }
                    else if (data.type === 'video_frame' && ws.clientType === 'web') {
                        this.wss.clients.forEach((client) => {
                            if (client.clientType === 'python' && client.readyState === WebSocket.OPEN) {
                                client.send(JSON.stringify({
                                    type: 'video',
                                    frame: data.frame
                                }));
                            }
                        });
                    }
                } catch (error) {
                    console.error('Error processing video message:', error);
                }
            });

            ws.on('close', () => {
                console.log('Client disconnected from video WebSocket');
            });
        });

        this.server.on('upgrade', (request, socket, head) => {
            if (request.url !== '/video-socket') {
                this.wss.handleUpgrade(request, socket, head, (ws) => {
                    this.wss.emit('connection', ws, request);
                });
            }
        });
    }
    start(port = 8081) {
        this.server.listen(port, 'localhost', () => {
            console.log(`Server running on port ${port}`);
            console.log(`Video WebSocket service available at /video-socket`);
            console.log(`Face detection service available at /upload`);
            console.log(`Message WebSocket service available at /messages`);
        });
    }
}

const server = new ApplicationServer();
server.start();

module.exports = ApplicationServer;