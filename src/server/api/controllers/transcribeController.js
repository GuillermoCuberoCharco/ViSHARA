const { transcribeAudio } = require('../../services/googleSTT');
const { getOpenAIResponse } = require('../../services/openAI');

async function handleTranscribe(req, res, messageIo) {
    try {
        const audio = req.body.audio;

        if (!audio) {
            return res.status(400).json({ error: 'No audio provided' });
        }

        const transcription = await transcribeAudio(audio);

        if (!transcription) {
            return res.status(200).json({
                continue: true,
                state: "Sad",
                text: ""
            });
        }

        const response = await getOpenAIResponse(transcription, {
            username: req.user.username || 'Desconocido',
            proactive_question: req.body.proactive_question || 'Ninguna',
        });

        if (response.text?.trim()) {
            messageIo.emit('client_message', {
                text: transcription,
                state: response.state
            });
            messageIo.emit('robot_message', {
                text: response.text,
                state: response.robot_mood
            });
        }

        res.status(200).json(response);
    } catch (error) {
        console.error('Error transcribing audio:', error);
        res.status(500).json({ error: 'Error transcribing audio' })
    }
}

module.exports = { handleTranscribe };