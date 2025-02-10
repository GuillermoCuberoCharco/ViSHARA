const textToSpeech = require('@google-cloud/text-to-speech');
require('dotenv').config();

const getCredentialsConfig = () => {
  const googleCreds = process.env.GOOGLE_APPLICATION_CREDENTIALS;

  try {
    const parsedCreds = JSON.parse(googleCreds);
    return { credentials: parsedCreds };
  } catch (e) {
    return { keyFilename: googleCreds };
  }
};

const synthesize = async (req, res) => {
  try {
    const credentialsConfig = getCredentialsConfig();
    const client = new textToSpeech.TextToSpeechClient(credentialsConfig);
    const text = req.body.text;

    const request = {
      input: { text: text },
      voice: {
        languageCode: 'es-ES',
        name: 'es-ES-Standard-C'
      },
      audioConfig: {
        audioEncoding: 'LINEAR16',
        effectsProfileId: ['medium-bluetooth-speaker-class-device'],
        pitch: 1.6,
        speakingRate: 1
      },
    };
    const [response] = await client.synthesizeSpeech(request);
    const audioContent = response.audioContent.toString('base64');

    res.json({ audioContent });
  } catch (error) {
    console.error('Error en la síntesis de voz:', error);
    res.status(500).json({ error: error.message });
  }
};

module.exports = synthesize;