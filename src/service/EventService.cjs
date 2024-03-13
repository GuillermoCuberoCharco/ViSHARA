const express = require('express');
const axios = require('axios');
const cors = require('cors');
const bodyParser = require('body-parser');
const app = express();
const synthesize = require('./googleTTS.cjs');
const transcribe = require('./googleSTT.cjs');
const upload = require('./cameraService.cjs');
const candidates = require('./candidateHandler.cjs');
const response = require('./responseHandler.cjs');

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

//Google TTS service
app.post("/synthesize", synthesize);
//Google STT servicie
app.post('/transcribe', transcribe);
//Camera service
app.post('/upload', upload);
//WebRTC candidates service
app.post('/candidates', candidates.post);
app.get('/candidates', candidates.get);
//WebRTC response service
app.post('/response', response.post);
app.get('/response', response.get);

// WebSocket server
const WebSocket = require('ws');
const server = new WebSocket.Server({ port: 8081 });
const connections = new Set();

server.on('connection', (socket) => {
    connections.add(socket);

    socket.on('message', (message) => {
        console.log('Comando recibido desde la terminal:', message.toLocaleString());
        connections.forEach((client) => {
            if (client !== socket && client.readyState === WebSocket.OPEN) {
                client.send(message);
            }
        });
    });

    socket.on('close', () => {
        console.log('Terminal desconectada');
        connections.delete(socket);
    });
});

app.listen(8082, ()=>{
    console.log('Servidor de endpoints en el puerto 8082');
    console.log('Servidor de eventos iniciado en el puerto 8081');
})

