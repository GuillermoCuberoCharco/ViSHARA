// Imports the Google Cloud client library

process.env.GOOGLE_APPLICATION_CREDENTIALS = 'vishara-415010-002552ca9ca0.json';
const speech = require('@google-cloud/speech');
const client = new speech.SpeechClient();

async function transcribeAudio(audioContent) {

    const encoding = 'WEBM_OPUS';
    const sampleRateHertz = 48000;
    const languageCode = 'es-ES';

    const config = {
        encoding: encoding,
        sampleRateHertz: sampleRateHertz,
        languageCode: languageCode,
        audioChannelCount: 2,
    };
    const audio = {
        content: audioContent,
    };

    const request = {
    config: config,
    audio: audio,
    };

    const [response] = await client.recognize(request);
    return response;
}

module.exports = transcribeAudio;