const { transcribeAudio } = require('../../services/googleSTT.cjs');

async function handleTranscribe(req, res) {
    try {
        const audio = req.body.audio;

        if (!audio) {
            return res.status(400).json({ error: 'No audio provided' });
        }

        const transcription = await transcribeAudio(audio);

        if (!transcription || transcription.trim() === '') {
            return res.status(200).json('');
        }

        res.status(200).json(transcription);
    } catch (error) {
        console.error('Error transcribing audio:', error);
        res.status(500).json({ error: 'Error transcribing audio' })
    }
}

module.exports = { handleTranscribe };