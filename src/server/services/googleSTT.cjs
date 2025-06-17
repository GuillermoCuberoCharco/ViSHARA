const speech = require('@google-cloud/speech');
const config = require('../config/environment.cjs');

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

function getAutoConfig(audioContent) {
    const audioBuffer = Buffer.from(audioContent, 'base64');
    const isWAV = audioBuffer.slice(0, 4).toString() === 'RIFF' &&
        audioBuffer.slice(8, 12).toString() === 'WAVE';

    if (isWAV) {
        console.log('Using WAV config (wizard audio)');
        return {
            encoding: 'LINEAR16',
            sampleRateHertz: 48000,
            languageCode: 'es-ES',
            audioChannelCount: 1,
        };
    } else {
        console.log('Using WEBM_OPUS config (web client audio)');
        return {
            encoding: 'WEBM_OPUS',
            sampleRateHertz: 48000,
            languageCode: 'es-ES',
            audioChannelCount: 1,
        };
    }
}

async function transcribeAudio(audioContent) {
    try {

        const config = getAutoConfig(audioContent);

        const audio = {
            content: audioContent,
        };

        const request = {
            config: config,
            audio: audio,
        };

        console.log('Sending audio to Google Speech-to-Text...');
        const [response] = await client.recognize(request);

        if (!response || !response.results || response.results.length === 0) {
            console.log('No transcription results returned from Google Speech-to-Text');
            return null;
        }

        const transcription = response.results
            .map(result => result.alternatives[0].transcript)
            .join('\n')
            .trim();

        console.log('Transcription successful:', transcription);
        return transcription;

    } catch (error) {
        console.error('Error in Google Speech-to-Text transcription:', error);
        throw error;
    }
}



module.exports = {
    transcribeAudio
};