const axios = require('axios');
require('dotenv').config();

const synthesize = async (req, res) => {
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
};

module.exports = synthesize;