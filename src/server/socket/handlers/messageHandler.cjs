const { getOpenAIResponse } = require('../../services/opeanaiService.cjs');

function setupMessageHandlers(io) {
    io.on('connection', (socket) => {
        console.log('Client connected to message socket');

        socket.on('register_client', (cientType) => {
            console.log('Client registered', cientType);
            socket.emit('registration_success', { status: 'ok' });
        });

        socket.on('client_message', async (message) => {
            try {
                const parsed = typeof message === 'string' ? JSON.parse(message) : message;
                const inputText = parsed.text?.trim() || "";

                if (!inputText) {
                    console.log('Empty message received');
                    return;
                }

                const response = await getOpenAIResponse(inputText, {
                    username: parsed.username || 'Desconocido',
                    proactive_question: parsed.proactive_question || 'Ninguna',
                });

                if (response.text?.trim()) {
                    socket.emit('robot_message', {
                        text: response.text,
                        state: response.robot_mood
                    });
                }
            } catch (error) {
                console.error('Error processing message:', error);
                socket.emit('error', { message: 'Error processing message' });
            }
        });

        socket.on('disconnect', () => {
            console.log('Client disconnected from message socket');
        });
    });
}

module.exports = { setupMessageHandlers };