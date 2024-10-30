const express = require('express');
const cors = require('cors');
const { Server } = require('socket.io');
const bodyParser = require('body-parser');
const synthesize = require('./googleTTS.cjs');
const transcribe = require('./googleSTT.cjs');
const watsonService = require('./ibmWatsonService.cjs');
const faceTracker = require('./faceTracker.cjs');
const videoTracker = require('./videoTracker.cjs');
const http = require('http');

const app = express();
app.use(cors({
    origin: 'http://localhost:5173',
    methods: ['GET', 'POST'],
    credentials: true
}));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

const server = http.createServer(app);

const messageIo = new Server(server, {
    cors: {
        origin: 'http://localhost:5173',
        methods: ['GET', 'POST'],
        credentials: true
    },
    transports: ['websocket', 'polling'],
    pingTimeout: 60000,
    pingInterval: 25000,
    upgradeTimeout: 10000,
    allowUpgrades: true,
    path: '/socket.io/'
});

const videoIo = new Server(server, {
    path: '/video-socket',
    cors: {
        origin: 'http://localhost:5173',
        methods: ['GET', 'POST'],
        credentials: true
    },
    transports: ['websocket']
});

// Initialize all the services
watsonService.createSession().catch(console.error);
faceTracker.startCameraService(app, videoIo);
videoTracker.startVideoService(server, videoIo);

// Google TTS service
app.post("/synthesize", synthesize);
// Google STT servicie
app.post('/transcribe', transcribe);

let pythonClient = null;

// Unified WebSocket handling
messageIo.on('connection', (socket) => {
    console.log('New WebSocket connected');

    socket.on('register_python_client', () => {
        console.log('Python client registered:', socket.id);
        pythonClient = socket.id;
        socket.emit('registration_confirmed');
    });

    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
        if (socket.id === pythonClient) {
            console.log('Python client disconnected');
            pythonClient = null;
        }
    });

    socket.on('message', async (message) => {
        console.log('Received message:', message);

        let parsedMessage = typeof message === 'string' ? JSON.parse(message) : message;

        if (parsedMessage.type === 'client_message') {
            console.log('Received client message:', parsedMessage.text);

            // Send the message to the client
            messageIo.emit('client_message', {
                text: parsedMessage.text,
                state: parsedMessage.state
            });

            // Process the message with the Watson service
            try {
                const { response, userDefined, emotions, strongestEmotion } = await watsonService.getWatsonResponse(parsedMessage.text);
                const watsonText = response.output.generic[0].text;

                // Send the response to all connections
                if (response && pythonClient) {
                    messageIo.to(pythonClient).emit('watson_message', {
                        text: watsonText,
                        emotions: emotions,
                        state: strongestEmotion
                    });
                } else if (pythonClient) {
                    messageIo.to(pythonClient).emit('watson_message', {
                        text: 'Sorry, I did not understand that',
                        state: 'Confused'
                    });
                }
            } catch (error) {
                console.error('Error processing message:', error);
            }
        } else if (parsedMessage.type === 'wizard_message') {
            console.log('Received wizard message:', parsedMessage.text);
            messageIo.emit('wizard_message', {
                text: parsedMessage.text,
                state: parsedMessage.state
            });
        }
    });
});

const PORT = process.env.PORT || 8081;
server.listen(PORT, 'localhost', () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Video WebSocket service available at /video-socket`);
    console.log(`Face detection service available at /upload`);
});

