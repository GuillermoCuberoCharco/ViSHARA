const { getOpenAIResponse } = require('../../services/opeanaiService.cjs');
const { updateUserName, findUserByName } = require('../../services/faceRecognitionService.cjs');

const pendingIdentifications = new Map();
const userSessions = new Map();

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

        socket.on('user_detected', (userData) => {
            console.log('User detected:', userData);
            const session = userSessions.get(socket.id || {});
            session.currentUserId = userData.userId;
            session.lastFaceUpdate = Date.now();
            userSessions.set(socket.id, session);

            if (userData.needsIdentification && !pendingIdentifications.has(userData.userId)) {
                pendingIdentifications.set(userData.userId, {
                    socketId: socket.id,
                    waitingForName: false,
                    tempUserId: userData.userId
                });

                setTimeout(() => {
                    sendProactiveIdentification(socket, userData.userId);
                }, 2000)
            }
        })

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

                const pending = currentUserId ? pendingIdentifications.get(currentUserId) : null;
                if (pending && pending.waitingForName) {
                    const result = await processNameResponse(inputText, currentUserId, socket);
                    if (result.success) {
                        context.username = result.userName;
                        context.proactive_question = 'who_are_you_response';

                        pendingIdentifications.delete(currentUserId);

                        if (result.newUserId) {
                            session.currentUserId = result.newUserId;
                            userSessions.set(socket.id, session);
                        }
                    } else {
                        context.proactive_question = 'who_are_you';
                    }
                } else if (currentUserId && context.username === 'Desconocido') {
                    const userInfo = await getUserInfo(currentUserId);
                    if (userInfo && userInfo.userName && userInfo.userName !== 'unknown') {
                        context.username = userInfo.userName;
                    }
                }

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
                }
            } catch (error) {
                console.error('Error processing message:', error);
                socket.emit('error', { message: 'Error processing message' });
            }
        });

        socket.on('message', (message) => {
            try {
                console.log('Received wizard message:', message);
                socket.broadcast.emit('wizard_message', {
                    text: message.text,
                    state: message.state
                });

                socket.emit('message_received', { status: 'ok' });
            } catch (error) {
                console.error('Error processing message:', error);
                socket.emit('error', { message: 'Error processing message' });
            }
        });

        socket.on('disconnect', () => {
            console.log('Client disconnected from message socket');

            const session = userSessions.get(socket.id);
            if (session && session.currentUserId) {
                const pending = pendingIdentifications.get(session.currentUserId);
                if (pending && pending.socketId === socket.id) {
                    pendingIdentifications.delete(session.currentUserId);
                }
            }
            userSessions.delete(socket.id);
        });
    });
}

async function sendProactiveIdentification(socket, userId) {
    try {
        const response = await getOpenAIResponse('', {
            username: 'Desconocido',
            proactive_question: 'who_are_you'
        });

        if (response.text?.trim()) {
            console.log(`Sending proactive identification for user ${userId}:`, response.text);

            const pending = pendingIdentifications.get(userId);
            if (pending) {
                pending.waitingForName = true;
                pendingIdentifications.set(userId, pending);
            }

            socket.emit('robot_message', {
                text: response.text,
                state: response.robot_mood
            });

            socket.broadcast.emit('openai_message', {
                text: response.text,
                state: response.robot_mood
            });
        }
    } catch (error) {
        console.error('Error sending proactive identification:', error);
    }
}

async function processNameResponse(inputText, userId, socket) {
    try {
        const extractedName = extractNameFromResponse(inputText);

        if (!extractedName) {
            console.log('Invalid name response:', inputText);
            return { success: false };
        }

        const existingUser = await findUserByName(extractedName);
        if (existingUser && existingUser.userId !== userId) {
            console.log(`User ${existingUser.userName} already exists with ID ${existingUser.userId}`);
        }

        const result = await updateUserName(userId, extractedName);

        if (result.success) {
            console.log(`User ${userId} updated with name ${extractedName}`);
            return { success: true, userName: extractedName, newUserId: result.newUserId !== userId ? result.newUserId : null };
        } else {
            console.log(`Failed to update user ${userId} with name ${extractedName}`);
            return { success: false };
        }
    } catch (error) {
        console.error('Error processing name response:', error);
        return { success: false };
    }
}

function extractNameFromResponse(response) {
    const patterns = [
        /(?:me llamo|soy|mi nombre es)\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)*)/i,
        /^([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)*)$/i,
        /(?:llamo|nombre)\s+([a-záéíóúñ]+)/i,
    ];

    const cleanText = text.trim().toLowerCase();

    for (const pattern of patterns) {
        const match = cleanText.match(pattern);
        if (match && match[1]) {
            return match[1]
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ')
                .trim();
        }
    }

    return null;
}

async function getUserInfo(userId) {
    return null
}

module.exports = { setupMessageHandlers };