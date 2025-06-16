const { transcribeAudio } = require('../../services/googleSTT.cjs');

function setupVoiceHandlers(io) {
    io.on('connection', (socket) => {

        socket.on('voice_response', async (data) => {
            try {
                console.log('Received voice response data from wizard');

                const audioBuffer = Buffer.from(data.audio, 'base64');
                const transcription = await transcribeAudio(audioBuffer);

                if (!transcription) throw new Error('Transcription failed or returned no results');

                console.log('Transcription result:', transcription);

                const clientSocket = Array.from(io.sockets.sockets.values()).find(s => !s.isWizardOperator && s.connected);

                if (clientSocket) {
                    clientSocket.emit('openai_message', {
                        text: transcription,
                        robot_mood: data.robot_state || 'Attention',
                        continue: true,
                        source: 'wizard_voice'
                    });

                    console.log(`Response sent to client: ${transcription}`);
                }

                socket.emit('voice_response_confirmation', { success: true });
            } catch (error) {
                console.error('Error processing voice response:', error);
                socket.emit('voice_response_confirmation', { success: false, error: error.message });
            }
        });

        socket.on('register_operator', () => {
            socket.isWizardOperator = true;
        });
    });
}

module.exports = { setupVoiceHandlers };