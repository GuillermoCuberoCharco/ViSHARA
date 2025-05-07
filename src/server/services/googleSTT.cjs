// Imports the Google Cloud client library
const speech = require('@google-cloud/speech');
const config = require('../config/environment.cjs')

let client;

try {
    const credentials = JSON.parse(config.google.credentials);
    client = new speech.SpeechClient({
        credentials: credentials
    });
} catch (error) {
    client = new speech.SpeechClient({
        keyFilename: config.google.credentials
    });
}

async function transcribeAudio(audioContent) {

    const encoding = 'WEBM_OPUS';
    const sampleRateHertz = 48000;
    const languageCode = 'es-ES';

    const config = {
        encoding: encoding,
        sampleRateHertz: sampleRateHertz,
        languageCode: languageCode,
        audioChannelCount: 1,
    };
    const audio = {
        content: audioContent,
    };

    const request = {
        config: config,
        audio: audio,
    };

    const [response] = await client.recognize(request);

    if (!response || !response.results || response.results.length === 0) {
        console.log('No transcription results returned');
        return;
    }

    const transcription = response.results
        .map(result => result.alternatives[0].transcript)
        .join('\n');

    return transcription;
}

module.exports = { transcribeAudio };