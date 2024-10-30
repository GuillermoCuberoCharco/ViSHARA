const axios = require('axios');
const ffmpeg = require('fluent-ffmpeg');
const fs = require('fs');
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
  // Save the audio content to a file for debbuging purposes
  // const audio = response.data.audioContent;
  // const audioBuffer = Buffer.from(audio, 'base64');

  // fs.writeFile('src/tests/output_mono.wav', audioBuffer, (err) => {
  //   if (err) throw err;
  //   console.log('Audio content has been saved as output.wav');
  // });

  // ffmpeg('src/tests/output_mono.wav')
  //   .outputOption('-ac 2')
  //   .save('src/tests/output_stereo.wav')
  //   .on('end', () => {
  //     console.log('Audio content has been saved as output_stereo.wav');
  //   });
  // Return the audio content to the client
  res.json(response.data);
};

module.exports = synthesize;