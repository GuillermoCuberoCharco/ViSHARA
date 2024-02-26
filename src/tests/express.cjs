const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(
    cors({})
);


app.get("/", (req, res) => {
    res.send("Servidor de síntesis de voz");
},);

app.post("/synthesize", async (req, res) => {
    const text = req.body.text;
    const apiKey = "AIzaSyAm4WlilenpBXTYkc1RefU8plElIxnFjD4";
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

const port = 3000;
app.listen(port, ()=>{
    console.log(`Servidor de síntesis de voz iniciado en el puerto ${port}`);
})