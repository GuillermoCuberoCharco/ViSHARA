import { getOpenAIResponse } from './opeanaiService.cjs';

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


// Initialize all the services
watsonService.createSession().catch(console.error);
faceTracker.startCameraService(app, videoIo);
videoTracker.startVideoService(server);

// Google TTS service
app.post("/synthesize", synthesize);
// Google STT servicie
app.post('/transcribe', async (req, res) => {
    try {
        await transcribe(req, res);
        const transcription = req.locals.transcription;

        if (transcription && messageIo) {
            const response = await getOpenAIResponse(transcription, {
                username: req.body.username || 'Desconocido',
                proactive_question: req.body.proactive_question || 'Nunguna'
            });

            messageIo.emit('client_message', {
                text: transcription,
                state: response.state
            });

            messageIo.emit('watson_message', {
                text: response.text,
                state: response.robot_mood
            });

            res.status(200).json(response);
        }
    } catch (error) {
        console.error('Error transcribing audio:', error);
        res.status(500).json({ error: 'Error transcribing audio' });
    }
});

const messageIo = new Server(server, {
    cors: {
        origin: true,
        methods: ['GET', 'POST'],
        credentials: true
    },
    transports: ['polling', 'websocket'],
    allowUpgrades: true,
    upgradeTimeout: 10000,
    pingTimeout: 5000,
    pingInterval: 10000
});

// Unified WebSocket handling
messageIo.on('connection', (socket) => {
    socket.on('message', async (message) => {
        const parsed = JSON.parse(message);

        if (parsed.type === 'client_message') {
            const response = await getOpenAIResponse(parsed.text, {
                username: parsed.username,
                proactive_question: parsed.proactive_question
            });

            socket.emit('watson_message', {
                text: response.text,
                state: response.robot_mood
            });
        }
    });
});

const PORT = process.env.PORT || 8081;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Video WebSocket service available at /video-socket`);
    console.log(`Face detection service available at /upload`);
});