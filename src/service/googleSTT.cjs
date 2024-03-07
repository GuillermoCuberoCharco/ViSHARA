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

const transcribe = async (req, res) => {
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
};

module.exports = transcribe;