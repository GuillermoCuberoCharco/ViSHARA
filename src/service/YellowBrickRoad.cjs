const express = require('express');
const cors = require('cors');
const socketIo = require('socket.io');
const bodyParser = require('body-parser');
const synthesize = require('./googleTTS.cjs');
const transcribe = require('./googleSTT.cjs');
const watsonService = require('./ibmWatsonService.cjs');
const faceTracker = require('./faceTracker.cjs');
const videoTracker = require('./videoTracker.cjs');
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

// Initialize the all services
watsonService.createSession().catch(console.error);
faceTracker.startCameraService(app, io);
videoTracker.startVideoService(server, io);

// Google TTS service
app.post("/synthesize", synthesize);
// Google STT servicie
app.post('/transcribe', transcribe);

let pythonClient = null;

// Unified WebSocket handling
io.on('connection', (socket) => {
    console.log('New WebSocket connected');

    socket.on('register_python_client', () => {
        console.log('Python client registered:', socket.id);
        pythonClient = socket.id;
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

        let parsedMessage = message;
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
                    if (pythonClient) {
                        io.to(pythonClient).emit('watson_message', {
                            text: watsonText,
                            emotions: emotions,
                            state: strongestEmotion
                        });
                    } else {
                        console.log('No Python client connected');
                    }
                } else {
                    // Send a 'No response' message if Watson doesn't understand the input
                    if (pythonClient) {
                        io.to(pythonClient).emit('watson_message', {
                            text: 'Sorry, I did not understand that',
                            state: 'Confused'
                        });
                    } else {
                        console.log('No Python client connected');
                    }
                }
            } catch (error) {
                console.error('Error processing message:', error);
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
    console.log(`Video WebSocket service available at /video-socket`);
    console.log(`Face detection service available at /upload`);
});

