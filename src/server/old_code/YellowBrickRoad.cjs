const express = require('express');
const cors = require('cors');
const { Server } = require('socket.io');
const bodyParser = require('body-parser');
const synthesize = require('../services/googleTTS.js');
const transcribe = require('../services/googleSTT.js');
const { getOpenAIResponse } = require('../services/opeanaiService.js');
const faceTracker = require('./faceTracker.cjs');
const videoTracker = require('./videoTracker.cjs');
const http = require('http');

const app = express();
app.use(cors({
    origin: true,
    methods: ['GET', 'POST'],
    credentials: true
}));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

const server = http.createServer(app);

const videoIo = new Server(server, {
    path: '/video-socket',
    cors: {
        origin: true,
        methods: ['GET', 'POST'],
        credentials: true
    },
    transports: ['websocket']
});

const messageIo = new Server(server, {
    cors: {
        origin: true,
        methods: ['GET', 'POST'],
        credentials: true
    },
    transports: ['polling', 'websocket']
});

// Initialize all the services
faceTracker.startCameraService(app, videoIo);
videoTracker.startVideoService(server);

// Google TTS service
app.post("/synthesize", synthesize);
// Google STT servicie
app.post('/transcribe', async (req, res) => {
    try {
        await transcribe(req, res);
        const transcription = res.locals.transcript?.trim() || "";

        if (!transcription) {
            console.log('No transcription available');
            return res.status(200).json({
                continue: true,
                state: "Sad",
                text: ""
            });
        }

        const response = await getOpenAIResponse(transcription, {
            username: req.body.username || 'Desconocido',
            proactive_question: req.body.proactive_question || 'Ninguna'
        });

        if (response.response?.trim()) {
            messageIo.emit('client_message', {
                text: transcription,
                state: response.state
            });

            messageIo.emit('robot_message', {
                text: response.text,
                state: response.robot_mood
            });
        }

        res.status(200).json(response);

    } catch (error) {
        console.error('Error transcribing audio:', error);
        res.status(500).json({ error: 'Error transcribing audio' });
    }
});

// Unified WebSocket handling
messageIo.on('connection', (socket) => {
    socket.on('register_client', (clientType) => {
        console.log(`Client registered: ${clientType}`);
        socket.emit('registration_success', { status: 'ok' });
    });
    socket.on('message', async (message) => {
        const parsed = typeof message === 'string' ? JSON.parse(message) : message;

        if (parsed.type === 'client_message') {
            const inputText = parsed.text?.trim() || "";

            if (!inputText) {
                console.log('No input text available');
                return;
            }

            const response = await getOpenAIResponse(inputText, {
                username: parsed.username,
                proactive_question: parsed.proactive_question
            });

            if (response.response?.trim()) {
                socket.emit('robot_message', {
                    text: response.response,
                    state: response.robot_mood
                });
            }
        }
    });
});

const PORT = process.env.PORT || 8081;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Video WebSocket service available at /video-socket`);
    console.log(`Face detection service available at /upload`);
});