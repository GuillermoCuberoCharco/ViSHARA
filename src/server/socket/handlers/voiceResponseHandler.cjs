const { transcribeAudio } = require('../../services/googleSTTService.cjs');

/**
 * Configure the voice response handlers for the wizard operators
 */
function setupVoiceHandlers(io) {
    io.on('connection', (socket) => {
        console.log('New voice connection: ', socket.id);

        // Manejar registro de operadores wizard
        socket.on('register_operator', (data) => {
            console.log('Operator present for the interaction:', socket.id);
            socket.isWizardOperator = true;
            socket.emit('registration_confirmed', { status: 'ok' });
        });

        // Handle voice response from wizard
        socket.on('voice_response', async (data) => {
            await handleVoiceResponse(io, socket, data);
        });

        socket.on('disconnect', () => {
            console.log('Disconnecting...:', socket.id);
        });
    });
}

/**
 * Processes the voice response from a wizard operator
 */
async function handleVoiceResponse(io, wizardSocket, data) {
    try {
        console.log(`Processing wizard voice message ${wizardSocket.id}`);

        const audioBuffer = Buffer.from(data.audio, 'base64');
        console.log(`Dec. Audio of: ${audioBuffer.length} bytes`);

        const transcription = await transcribeAudio(audioBuffer);

        if (!transcription || transcription.trim().length === 0) {
            throw new Error('Error transcribing audio: no transcription received');
        }

        console.log(`Transcription compleated: "${transcription}"`);

        const clientSocket = findActiveClientSocket(io);

        if (!clientSocket) {
            throw new Error('No web client connected to send the response');
        }

        const robotResponse = {
            text: transcription,
            robot_mood: data.robot_state || 'Attention',
            continue: true,
            source: 'wizard'
        };

        clientSocket.emit('openai_message', robotResponse);
        console.log(`Sending response to client ${clientSocket.id}: "${transcription}"`);

        wizardSocket.emit('voice_response_confirmation', {
            success: true,
            transcription: transcription
        });

    } catch (error) {
        console.error('Error proccessing voice:', error);
        wizardSocket.emit('voice_response_confirmation', {
            success: false,
            error: error.message
        });
    }
}

/**
 * Searches for an active client socket that is not a wizard operator
 */
function findActiveClientSocket(io) {
    const sockets = Array.from(io.sockets.sockets.values());

    return sockets.find(socket =>
        !socket.isWizardOperator &&
        socket.connected
    );
}

module.exports = { setupVoiceHandlers };