const express = require('express');
const cors = require('cors');
const socketIo = require('socket.io');
const bodyParser = require('body-parser');
const synthesize = require('./googleTTS.cjs');
const transcribe = require('./googleSTT.cjs');
const watsonService = require('./ibmWatsonService.cjs');
const cameraService = require('./cameraService.cjs');
const { setupWebRTC } = require('./webrtcService.cjs');
const app = express();
const http = require('http');
const server = http.createServer(app);


app.use(cors({
    origin: 'http://localhost:5173',
    methods: ['GET', 'POST'],
    credentials: true
}));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

const io = socketIo(server, {
    cors: {
        origin: 'http://localhost:5173',
        methods: ['GET', 'POST'],
        credentials: true
    }
});

// Watson service
watsonService.createSession().catch(console.error);

// General configuration for socket.io
io.on('connection', (socket) => {
    console.log('A user connected');
    socket.on('disconnect', () => {
        console.log('User disconnected');
    });
});

// WebRTC service
const webrtcIo = setupWebRTC(server);

// Camera service for face detection
cameraService.startCameraService();


// Google TTS service
app.post("/synthesize", synthesize);
// Google STT servicie
app.post('/transcribe', transcribe);

// WebSocket server
const WebSocket = require('ws');
const ws_server = new WebSocket.Server({ port: 8081 });
const connections = new Set();

ws_server.on('connection', (socket) => {
    connections.add(socket);

    socket.on('message', async (message) => {
        let parsedMessage;
        try {
            parsedMessage = JSON.parse(message);
        } catch (error) {
            console.error('Invalid JSON. ERROR:', error);
            return;
        }

        if (parsedMessage.type === 'client_message') {
            console.log('Client message:', parsedMessage.text);

            // Send the client message back to the client
            socket.send(JSON.stringify({
                type: 'client_message',
                text: parsedMessage.text,
                state: parsedMessage.state
            }));

            // Forward message to the Wizard of Oz
            connections.forEach((client) => {
                if (client !== socket && client.readyState === WebSocket.OPEN) {
                    client.send(JSON.stringify({
                        type: 'client_message',
                        text: parsedMessage.text,
                        state: parsedMessage.state
                    }));
                }
            });

            // Process the message with Watson
            try {
                const { response, userDefined, emotions, strongestEmotion } = await watsonService.getWatsonResponse(parsedMessage.text);

                if (response) {
                    const watsonText = response.output.generic[0].text;

                    // Send Watson response to all connections (including the Wizard of Oz)
                    connections.forEach((client) => {
                        if (client !== socket && client.readyState === WebSocket.OPEN) {
                            client.send(JSON.stringify({
                                type: 'watson_response',
                                text: watsonText,
                                emotions: emotions,
                                state: strongestEmotion
                            }));
                        }
                    });
                } else {

                    // Send a 'No response' message if Watson did not understand the input
                    connections.forEach((client) => {
                        if (client !== socket && client.readyState === WebSocket.OPEN) {
                            client.send(JSON.stringify({
                                type: 'watson_response',
                                text: 'Sorry, I did not understand that',
                                state: 'confused'
                            }));
                        }
                    });
                }
            } catch (error) {
                console.error('Error processing message with Watson:', error);
                connections.forEach((client) => {
                    if (client !== socket && client.readyState === WebSocket.OPEN) {
                        client.send(JSON.stringify({
                            type: 'watson_response',
                            text: 'Error processing message with Watson',
                            state: 'confused'
                        }));
                    }
                });
            }
        } else if (parsedMessage.type === 'wizard_message') {
            console.log('Wizard message:', parsedMessage.text);

            // Broadcast the Wizard message to other clients
            connections.forEach((client) => {
                if (client !== socket && client.readyState === WebSocket.OPEN) {
                    client.send(JSON.stringify({
                        type: 'wizard_message',
                        text: parsedMessage.text,
                        state: parsedMessage.state
                    }));
                }
            });
        }
    });

    socket.on('close', () => {
        console.log('Client disconnected');
        connections.delete(socket);
    });
});

server.listen(4000, () => {
    console.log('Main server running on port 4000');
    console.log('Face recognition server available at /upload');
    console.log('WebRTC server available at /webrtc');
});

app.listen(8082, () => {
    console.log('Express endpoints server running on port 8082');
    console.log('Websocket message server running on port 8081');
})

