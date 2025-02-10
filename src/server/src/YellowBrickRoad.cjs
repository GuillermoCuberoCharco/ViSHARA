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
        console.log('Transcribing audio');
        await transcribe(req, res);
        const transcription = res.locals.transcript;
        const state = res.locals.state;

        if (transcription && messageIo) {
            console.log('Sending transcription to clients with text:', transcription);
            messageIo.emit('client_message', {
                text: transcription,
                state: state
            });
            try {
                const { response, userDefined, emotions, strongestEmotion } =
                    await watsonService.getWatsonResponse(transcription);
                const watsonText = response.output.generic[0].text;

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
                console.error('Error processing Watson response:', error);
            }
        } else {
            console.log('No transcription to send');
            if (pythonClient) {
                messageIo.emit('client_message', {
                    text: '',
                    state: 'Sad'
                });
                messageIo.to(pythonClient).emit('watson_message', {
                    text: '',
                    state: 'Sad'
                });
            }
        }
    } catch (error) {
        console.error('Error in transcription route:', error);
        if (pythonClient) {
            messageIo.emit('client_message', {
                text: '',
                state: 'Sad'
            });
            messageIo.to(pythonClient).emit('watson_message', {
                text: '',
                state: 'Sad'
            });
        }
        res.status(500).json({ error: 'Failed to transcribe audio' });
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

let pythonClient = null;
let webClient = null;

// Unified WebSocket handling
messageIo.on('connection', (socket) => {
    console.log('New WebSocket connected');

    socket.on('register_client', (clientType) => {
        console.log(`Client registration attempt - Type: ${clientType}, ID: ${socket.id}`);

        if (clientType === 'python') {
            pythonClient = socket.id;
            console.log('Python client registered');
            socket.emit('registration_success', { type: 'python' });
        }
        else if (clientType === 'web') {
            webClient = socket.id;
            console.log('Web client registered');
            socket.emit('registration_success', { type: 'web' });
        }
    });

    socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
        if (socket.id === pythonClient) {
            pythonClient = null;
            console.log('Python client disconnected');
        } else if (socket.id === webClient) {
            webClient = null;
            console.log('Web client disconnected');
        }
    });

    socket.on('message', async (message) => {
        console.log('Received message from:', socket.id);

        // if (socket.id !== webClient && socket.id !== pythonClient) {
        //     console.log('Message rejected: sender not registered');
        //     return;
        // }

        console.log('Message:', message);

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
                    socket.to(pythonClient).emit('watson_message', {
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
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Video WebSocket service available at /video-socket`);
    console.log(`Face detection service available at /upload`);
});