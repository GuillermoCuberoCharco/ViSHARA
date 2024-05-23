const express = require('express');
const multer = require('multer');
const axios = require('axios');
const cors = require('cors');
const bodyParser = require('body-parser');
const app = express();
const http = require('http');
const synthesize = require('./googleTTS.cjs');
const transcribe = require('./googleSTT.cjs');


app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

//Google TTS service
app.post("/synthesize", synthesize);
//Google STT servicie
app.post('/transcribe', transcribe);

// WebSocket server
const WebSocket = require('ws');
const ws_server = new WebSocket.Server({ port: 8081 });
const connections = new Set();

ws_server.on('connection', (socket) => {
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

//Camera service
const server = http.createServer(app);
const storage = multer.memoryStorage();
const upload = multer({ storage: storage });
const wss = new WebSocket.Server({ server });

let wsClient = null;
wss.on('connection', (ws) => {
    wsClient = ws;
    ws.on('close', () => {
        wsClient = null;
    });
    console.log('Cliente conectado');
});

app.post('/upload', upload.single('video'), (req, res) => {
    if (!req.file) {
      return res.status(400).send('No file uploaded.');
    }
    const videoBuffer = req.file.buffer;
    if (wsClient && wsClient.readyState === WebSocket.OPEN) {
        wsClient.send(videoBuffer);
        console.log('Video enviado');
    }
    req.status(200).send('Video received');
});

server.listen(8084, () => {
    console.log('Servidor de carga de videos en el puerto 8084');
});

app.listen(8082, ()=>{
    console.log('Servidor de endpoints en el puerto 8082');
    console.log('Servidor de eventos iniciado en el puerto 8081');
})

