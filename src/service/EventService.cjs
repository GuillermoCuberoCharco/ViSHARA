const express = require('express');
const cors = require('cors');
const socketIo = require('socket.io');
const bodyParser = require('body-parser');
const synthesize = require('./googleTTS.cjs');
const transcribe = require('./googleSTT.cjs');
const watsonService = require('./ibmWatsonService.cjs');
const cameraService = require('./cameraService.cjs');
const { setupWebRTC } = require('./webrtcService.cjs');
const http = require('http');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: 'http://localhost:5173',
        methods: ['GET', 'POST'],
        credentials: true
    }
});


app.use(cors({
    origin: 'http://localhost:5173',
    methods: ['GET', 'POST'],
    credentials: true
}));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Watson service
watsonService.createSession().catch(console.error);

// WebRTC service
setupWebRTC(io);

// Camera service for face detection
cameraService.startCameraService(app, io);


// Google TTS service
app.post("/synthesize", synthesize);
// Google STT servicie
app.post('/transcribe', transcribe);

// Unified WebSocket handling
io.on('connection', (socket) => {
    console.log('New WebSocket connected');

    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
    });

    socket.on('message', async (message) => {
        console.log('Received message:', message);

        if (typeof message === 'string') {
            try {
                parsedMessage = JSON.parse(message);
            } catch (error) {
                console.error('Error parsing message:', error);
                return;
            }
        }

        if (parsedMessage.type === 'client_message') {
            console.log('Received client message:', parsedMessage.text);

            // Send the message to the client
            socket.emit('client_message', {
                text: parsedMessage.text,
                state: parsedMessage.state
            });

            // Broadcast the message to all other clients (Wizzard of Oz)
            socket.broadcast.emit('client_message', {
                text: parsedMessage.text,
                state: parsedMessage.state
            });

            // Process the message with the Watson service
            try {
                const { response, userDefined, emotions, strongestEmotion } = await watsonService.getWatsonResponse(parsedMessage.text);
                if (response) {
                    const watsonText = response.output.generic[0].text;

                    // Send the response to all connections
                    io.emit('watson_message', {
                        text: watsonText,
                        emotions: emotions,
                        state: strongestEmotion
                    });
                } else {
                    // Send a 'No response' message if Watson doesn't understand the input
                    io.emit('watson_message', {
                        text: 'Sorry, I did not understand that',
                        state: 'Confused'
                    });
                }
            } catch (error) {
                console.error('Error processing message:', error);
                io.emit('watson_message', {
                    text: 'Error processing message with Watson',
                    state: 'Confused'
                });
            }
        } else if (parsedMessage.type === 'wizard_message') {
            console.log('Received wizard message:', parsedMessage.text);
            io.emit('wizard_message', {
                text: parsedMessage.text,
                state: parsedMessage.state
            });
        }
    });
});

const PORT = process.env.PORT || 8081;
server.listen(PORT, 'localhost', () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`WebRTC and WebSocket services available at /webrtc`);
    console.log(`Face detection service available at /upload`);
});

