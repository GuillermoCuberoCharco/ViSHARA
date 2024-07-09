const express = require('express');
const cors = require('cors');
const socketIo = require('socket.io');
const bodyParser = require('body-parser');
const cameraService = require('./cameraService.cjs');
const synthesize = require('./googleTTS.cjs');
const transcribe = require('./googleSTT.cjs');
const watsonService = require('./ibmWatsonService.cjs');
const app = express();
const http = require('http');
const server = http.createServer(app);
const io = socketIo(server);

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Watson service
watsonService.createSession().catch(console.error);

// Camera service
io.on('connection', (socket) => {
    console.log('A user connected');
    socket.on('disconnect', () => {
        console.log('User disconnected');
    });
});

server.listen(4000, () => {
    console.log('Server running on port 4000');
    cameraService.startCameraService();
});

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

            // Forward message to the Wizard of Oz
            connections.forEach((client) => {
                if (client !== socket && client.readyState === WebSocket.OPEN) {
                    client.send(JSON.stringify({
                        type: 'client_message',
                        text: parsedMessage.text
                    }));
                }
            });

            // Process the message with Watson
            try {
                const { response, userDefined, mood } = await watsonService.getWatsonResponse(parsedMessage.text);

                if (response) {
                    const watsonText = response.output.generic[0].text;
                    const emotionAnalysis = userDefined?.emotion || mood;

                    // Send Watson response to all connections (including the Wizard of Oz)
                    connections.forEach((client) => {
                        if (client !== socket && client.readyState === WebSocket.OPEN) {
                            client.send(JSON.stringify({
                                type: 'watson_response',
                                text: watsonText,
                                emotion: emotionAnalysis,
                                mood: mood
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
                                emotion: 'confused'
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
                            text: 'Error processing message with Watson'
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
                        text: parsedMessage.text
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


app.listen(8082, () => {
    console.log('Enpoints server 8082');
    console.log('Message server 8081');
})

