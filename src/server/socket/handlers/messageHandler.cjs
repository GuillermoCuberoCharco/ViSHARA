const { getOpenAIResponse } = require('../../services/opeanaiService.cjs');

function setupMessageHandlers(io) {
    io.on('connection', (socket) => {
        console.log('Client connected to message socket');

        socket.on('register_operator', (clientType) => {
            console.log('Message client registered', clientType, socket.id);
            socket.emit('registration_confirmed', { status: 'ok' });
        });

        socket.on('register_client', (clientType) => {
            console.log('Message client registered', clientType, socket.id);
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
                console.log('Received message:', inputText);

                const context = {
                    username: parsed.username || 'Desconocido',
                    proactive_question: parsed.proactive_question || 'Ninguna',
                };

                console.log('Processing message with context:', context);

                const response = await getOpenAIResponse(inputText, context);

                if (response.text?.trim()) {
                    console.log('Sending robot response:', response);

                    socket.emit('robot_message', {
                        text: response.text,
                        state: response.robot_mood
                    });

                    socket.broadcast.emit('openai_message', {
                        text: response.text,
                        state: response.robot_mood
                    });

                    if (response.robot_mood) {
                        console.log('Emitting animation state:', response.robot_mood);
                        io.of('/animation-socket').emit('animation_state', {
                            state: response.robot_mood
                        });
                    }
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