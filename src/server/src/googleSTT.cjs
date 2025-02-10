// Imports the Google Cloud client library
const speech = require('@google-cloud/speech');
require('dotenv').config();

let client;

try {
    const credentials = JSON.parse(process.env.GOOGLE_APPLICATION_CREDENTIALS);
    client = new speech.SpeechClient({
        credentials: credentials
    });
} catch (error) {
    client = new speech.SpeechClient({
        keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS
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

const transcribe = async (req, res) => {
    try {
        const audio = req.body.audio;
        const state = req.body.state;
        const response = await transcribeAudio(audio);
        const transcription = response.results.map(result => result.alternatives[0].transcript)
            .join('\n');
        res.locals.transcript = transcription;
        res.locals.state = state;

        res.json({ transcript: transcription, state: state });
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: 'Failed to transcribe audio' });
    }
};

module.exports = transcribe;