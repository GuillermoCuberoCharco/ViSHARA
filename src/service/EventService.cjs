const express = require('express');
const axios = require('axios');
const cors = require('cors');
const app = express();
const transcribeAudio = require('./googleSTT.cjs');
const upload = require('./cameraService.cjs');
require('dotenv').config();


app.use(cors());

//Google TTS service
app.post("/synthesize", async (req, res) => {
    const text = req.body.text;
    const apiKey = process.env.GOOGLE_API_KEY;
    const endpoint = `https://texttospeech.googleapis.com/v1beta1/text:synthesize?key=${apiKey}`;
    const payload = {
        "audioConfig": {
          "audioEncoding": "LINEAR16",
          "effectsProfileId": [
            "medium-bluetooth-speaker-class-device"
          ],
          "pitch": 1.6,
          "speakingRate": 1
        },
        "input": {
          "text": text
        },
        "voice": {
          "languageCode": "es-ES",
          "name": "es-ES-Standard-C"
        }
      }

      const response = await axios.post(endpoint, payload);
      res.json(response.data);
});

//Google STT servicie
app.post('/transcribe', async (req, res) => {
  try {
    const audio = req.body.audio;
    const response = await transcribeAudio(audio);
    const transcription = response.results
    .map(result => result.alternatives[0].transcript)
    .join('\n');
    res.json({ transcript: transcription });
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'Failed to transcribe audio' });
  }
});

//Camera service
app.post('/upload', upload);
app.listen(8080, () => {
  console.log('Servidor de cámara iniciado en el puerto 8080');
});

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
    console.log('Servidor de síntesis de voz iniciado en el puerto 8082');
    console.log('Servidor de eventos iniciado en el puerto 8081');
})