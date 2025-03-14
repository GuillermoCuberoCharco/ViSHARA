const textToSpeech = require('@google-cloud/text-to-speech');
const config = require('../config/environment.cjs');

const getCredentialsConfig = () => {
  const googleCreds = config.google.credentials;

  try {
    const parsedCreds = JSON.parse(googleCreds);
    return { credentials: parsedCreds };
  } catch (e) {
    return { keyFilename: googleCreds };
  }
};

async function synthesizeText(text) {
  try {
    const credentialsConfig = getCredentialsConfig();
    const client = new textToSpeech.TextToSpeechClient(credentialsConfig);

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
    return response.audioContent.toString('base64');
  } catch (error) {
    console.error('Error en la síntesis de voz:', error);
    throw error;
  }
}

module.exports = { synthesizeText };