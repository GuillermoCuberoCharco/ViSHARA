const { getOpenAIResponse } = require('../../services/opeanaiService.cjs');
const { updateUserName, findUserByName, listAllUsers } = require('../../services/faceRecognitionService.cjs');
const { startNewSession, addMessage, getConversationContext, endCurrentSession } = require('../../services/conversationService.cjs');
const { transcribeAudio } = require('../../services/googleSTT.cjs');

const pendingIdentifications = new Map();
const userSessions = new Map();
let OPERATOR_CONNECTED = false;

async function processClientMessage(inputText, socketId, io, customSocket = null) {
    try {
        if (!inputText || !inputText.trim()) {
            console.log('Empty message received');
            return;
        }

        console.log('Processing message:', inputText);

        const session = userSessions.get(socketId) || {};
        const currentUserId = session.currentUserId;

        if (currentUserId) {
            await addMessage(currentUserId, 'user', inputText, {
                socketId: socketId,
                messageType: 'client_message'
            });
        }

        let context = {
            username: 'Desconocido',
            proactive_question: 'Ninguna',
        };

        const pending = currentUserId ? pendingIdentifications.get(currentUserId) : null;
        if (pending && pending.waitingForName) {
            const result = await processNameResponse(inputText, currentUserId, customSocket || io.sockets.sockets.get(socketId));
            if (result.success) {
                context.username = result.userName;
                context.proactive_question = 'who_are_you_response';

                pendingIdentifications.delete(currentUserId);

                if (result.newUserId) {
                    session.currentUserId = result.newUserId;
                }

                session.currentUserName = result.userName;
                userSessions.set(socketId, session);

                console.log(`Session updated: user ${session.currentUserId} now identified as ${result.userName}`);

                if (currentUserId) {
                    await addMessage(currentUserId, 'user', inputText, {
                        messageType: 'identification_response',
                        extractedName: result.userName
                    });
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

        let conversationHistory = [];
        if (currentUserId) conversationHistory = getConversationContext(currentUserId, 15);

        console.log('Processing message with context:', context);
        console.log('Conversation history loaded:', conversationHistory.length, 'messages');

        const response = await getOpenAIResponse(inputText, context, conversationHistory);

        if (response.text?.trim()) {
            console.log('Sending robot response:', response);

            if (currentUserId) {
                await addMessage(currentUserId, 'assistant', response.text, {
                    mood: response.robot_mood,
                    messageType: 'robot_response'
                });
            }

            if (!OPERATOR_CONNECTED) {
                console.log('No operator connected, sending response to client socket:', socketId);
                const targetSocket = customSocket || io.sockets.sockets.get(socketId);
                if (targetSocket) {
                    targetSocket.emit('robot_message', {
                        text: response.text,
                        state: response.robot_mood
                    });
                }
            }

            io.emit('openai_message', {
                text: response.text,
                state: response.robot_mood
            });
        }
    } catch (error) {
        console.error('Error processing message:', error);
        const targetSocket = customSocket || io.sockets.sockets.get(socketId);
        if (targetSocket) {
            targetSocket.emit('error', { message: 'Error processing message' });
        }
    }
}

function setupMessageHandlers(io) {
    io.on('connection', (socket) => {
        console.log('Client connected to message socket');

        socket.on('register_operator', (clientType) => {
            socket.isWizardOperator = true;
            OPERATOR_CONNECTED = true;
            console.log('Message client registered', clientType, socket.id);
            socket.emit('registration_confirmed', { status: 'ok' });
        });

        socket.on('voice_response', async (data) => {
            await handleVoiceResponse(io, socket, data);
        });

        socket.on('register_client', (clientType) => {
            socket.isWizardOperator = false;
            console.log('Message client registered', clientType, socket.id);
            socket.emit('registration_success', { status: 'ok' });
        });

        socket.on('user_detected', async (userData) => {
            console.log('User detected:', userData);
            const shouldGreet = false;

            let session = userSessions.get(socket.id);
            const previousUserId = session?.currentUserId;

            if (!session) {
                session = {};
                console.log('Creating new session for socket:', socket.id);
            }

            if (previousUserId && previousUserId !== userData.userId) {
                await endCurrentSession(previousUserId);

                if (session.hasGreetedThisSession) {
                    if (!global.userSessionsEnds) global.userSessionsEnds = new Map();
                    global.userSessionsEnds.set(previousUserId, Date.now());
                    console.log(`Session ended for user ${previousUserId}, coldowned until next detection`);
                }
            }

            session.currentUserId = userData.userId;
            session.lastFaceUpdate = Date.now();

            if (!global.userSessionsEnds) global.userSessionsEnds = new Map();
            session.lastSessionEnd = global.userSessionsEnds.get(userData.userId);

            userSessions.set(socket.id, session);

            if (userData.userId !== previousUserId) {
                const sessionId = startNewSession(userData.userId);
                session.conversationSessionId = sessionId;

                const contextMessages = getConversationContext(userData.userId, 5);
                if (contextMessages.length > 0) {
                    console.log(`Loaded ${contextMessages.length} previous messages for context`);
                }
            }

            console.log('Session updated:', session);

            if (userData.needsIdentification && !pendingIdentifications.has(userData.userId)) {
                pendingIdentifications.set(userData.userId, {
                    socketId: socket.id,
                    waitingForName: false,
                    userId: userData.userId
                });

                setTimeout(() => {
                    sendProactiveMessage(socket, userData, 'who_are_you', () => {
                        const pending = pendingIdentifications.get(userData.userId);
                        if (pending) {
                            pending.waitingForName = true;
                            pendingIdentifications.set(userData.userId, pending);
                        }
                    });
                }, 2000);

            } else if (!userData.needsIdentification && userData.userName && userData.userName !== 'unknown') {
                console.log(`User ${userData.userId} already identified as ${userData.userName}`);
                const now = Date.now();
                const GREETING_COOLDOWN = 10 * 60 * 1000; // 10 minutes
                shouldGreet = false;

                if (userData.userId !== previousUserId) {
                    shouldGreet = true;
                    session.hasGreetedThisSession = false;
                    console.log(`New user detected, greeting them: ${userData.userName}`);
                } else if (!session.hasGreetedThisSession) {
                    const timeSinceLastSessionEnd = session.lastSessionEnd ? now - session.lastSessionEnd : Infinity;

                    if (timeSinceLastSessionEnd > GREETING_COOLDOWN) shouldGreet = true;
                }
            }

            if (shouldGreet) {
                session.hasGreetedThisSession = true;
                userSessions.set(socket.id, session);

                setTimeout(() => {
                    sendProactiveMessage(socket, userData, 'how_are_you');
                }, 2000);
            }
        });

        socket.on('user_lost', async (userData) => {
            console.log('User lost:', userData);

            if (userData.userId) {
                await endCurrentSession(userData.userId);
                console.log(`Session ended for lost user: ${userData.userId}`);
            }

            const session = userSessions.get(socket.id);
            if (session && session.currentUserId === userData.userId) {

                if (session.hasGreetedThisSession) {
                    if (!global.userSessionsEnds) global.userSessionsEnds = new Map();
                    global.userSessionsEnds.set(userData.userId, Date.now());
                    console.log(`Session ended for user ${userData.userId}, cooldown until next detection`);
                }

                session.currentUserId = null;
                session.conversationSessionId = null;
                session.hasGreetedThisSession = false;
                userSessions.set(socket.id, session);
            }
        })

        socket.on('client_message', async (message) => {
            try {
                const parsed = typeof message === 'string' ? JSON.parse(message) : message;

                if (parsed.type === 'audio') {
                    console.log('Received audio message from client for transcription');

                    const transcription = await transcribeAudio(parsed.data);

                    if (transcription && transcription.trim()) {
                        console.log('Transcription result:', transcription);

                        socket.emit('transcription_result', {
                            text: transcription,
                            processed: true
                        });

                        await processClientMessage(transcription, socket.id, io, socket);
                    } else {
                        console.log('No transcription result received');
                        socket.emit('transcription_result', {
                            text: '',
                            processed: false
                        });
                    }
                } else {
                    const inputText = parsed.text?.trim();
                    await processClientMessage(inputText, socket.id, io, socket);
                }
            } catch (error) {
                console.error('Error processing message:', error);
                socket.emit('error', { message: 'Error processing message' });
            }
        });

        socket.on('message', async (message) => {
            try {
                console.log('Received wizard message:', message);

                const session = userSessions.get(socket.id) || {};
                const currentUserId = session.currentUserId;

                if (currentUserId && message.text?.trim()) await addMessage(currentUserId, 'wizard', message.text, { state: message.state, messageType: 'wizard_message', socketId: socket.id });

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

        socket.on('disconnect', async () => {
            console.log('Client disconnected from message socket');
            OPERATOR_CONNECTED = false;

            const session = userSessions.get(socket.id);
            if (session && session.currentUserId) {
                await endCurrentSession(session.currentUserId);

                if (session.hasGreetedThisSession) {
                    if (!global.userSessionsEnds) global.userSessionsEnds = new Map();
                    global.userSessionsEnds.set(session.currentUserId, Date.now());
                    console.log(`Session ended for user ${session.currentUserId}, cooldown until next detection`);
                }

                for (const [userId, pending] of pendingIdentifications.entries()) {
                    if (pending.socketId === socket.id) {
                        pendingIdentifications.delete(userId);
                        break;
                    }
                }
            }
            userSessions.delete(socket.id);
        });
    });
}

async function sendProactiveMessage(socket, userData, proactiveQuestion, callback = null) {
    try {

        const conversationHistory = getConversationContext(userData.userId, 10);

        const response = await getOpenAIResponse('', {
            username: userData.userName || 'Desconocido',
            proactive_question: proactiveQuestion
        }, conversationHistory);

        if (response.text?.trim()) {
            console.log(`Sending proactive messsage (${proactiveQuestion}) for user ${userData.userId}:`, response.text);

            await addMessage(userData.userId, 'assistant', response.text, {
                mood: response.robot_mood,
                messageType: `proactive_${proactiveQuestion}`,
            });

            if (callback && typeof callback === 'function') callback();

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
        console.error(`Error sending proactive message (${proactiveQuestion}):`, error);
    }
}

async function processNameResponse(inputText, userId, socket) {
    try {
        const extractedName = extractNameFromResponse(inputText);

        if (!extractedName) {
            console.log('Could not extract name from response:', inputText);
            return { success: false };
        }

        const existingUser = findUserByName(extractedName);
        if (existingUser && existingUser.userId !== userId) {
            console.log(`Name ${extractedName} already exists for user ${existingUser.userId}`);
        }

        const result = await updateUserName(userId, extractedName);

        if (result.success) {
            console.log(`Successfully identified user ${userId} as ${extractedName}`);
            return {
                success: true,
                userName: extractedName,
                newUserId: result.userId !== userId ? result.userId : null
            };
        } else {
            console.error('Failed to update user name:', result.error);
            return { success: false };
        }
    } catch (error) {
        console.error('Error processing name response:', error);
        return { success: false };
    }
}

function extractNameFromResponse(text) {
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
    try {
        const allUsers = listAllUsers();
        const user = allUsers.find(u => u.userId === userId);

        if (user) {
            return {
                userId: user.userId,
                userName: user.userName,
                lastSeen: user.lastSeen,
                visits: user.visits,
                isTemporary: user.isTemporary
            };
        }
        return null;
    } catch (error) {
        console.error('Error getting user info:', error);
        return null;
    }
}

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
        console.log(`Robot state: ${data.robot_state}`);

        const clientSocket = Array.from(io.sockets.sockets.values()).find(socket => !socket.isWizardOperator && socket.connected);

        if (!clientSocket) {
            throw new Error('No web client connected to send the response');
        }

        console.log(`Sending response to client ${clientSocket.id}: "${transcription}"`);

        io.emit('robot_message', {
            text: transcription,
            state: data.robot_state
        });

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

module.exports = { setupMessageHandlers, processClientMessage };