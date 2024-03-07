const express = require('express');
const axios = require('axios');
const cors = require('cors');
const app = express();
app.use(cors());
const synthesize = require('./googleTTS.cjs');
const transcribe = require('./googleSTT.cjs');
const upload = require('./cameraService.cjs');

//Google TTS service
app.post("/synthesize", synthesize);
//Google STT servicie
app.post('/transcribe', transcribe);
//Camera service
app.post('/upload', upload);

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