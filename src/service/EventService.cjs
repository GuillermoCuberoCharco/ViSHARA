const express = require('express');
const axios = require('axios');
const cors = require('cors');
const bodyParser = require('body-parser');
const app = express();
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

//Camera service

const wss = new WebSocket.Server({ port: 8084 });

wss.on('connection', (ws) => {
  ws.on('message', message => {
    if (wss.clients.size > 2){
      wss.clients.forEach(client => {
        if (client !== ws && client.readyState === WebSocket.OPEN) {
          client.send(message);
        }
      });
    } else {
      console.log('No clients connected, discarding message');
    }
    
  });

  ws.on('close', () => {
    console.log('WebSocket connection closed');
  });
});



app.listen(8082, ()=>{
    console.log('Servidor de endpoints en el puerto 8082');
    console.log('Servidor de eventos iniciado en el puerto 8081');
})

