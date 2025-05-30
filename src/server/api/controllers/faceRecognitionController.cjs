const { recognizeFaceWithConfirmation, listAllUsers, debugDatabase, updateUserName } = require('../../services/faceRecognitionService.cjs');
const multer = require('multer');

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

const clientSessions = new Map();

let messageIo = null;
function setMessageSocketRef(io) {
    messageIo = io.messageIo;
}

function getOrCreateSessionId(clientId) {
    if (!clientSessions.has(clientId)) {
        const sessionId = `session_${Date.now()}_${clientId}_${Math.random().toString(36).substr(2, 9)}`;
        clientSessions.set(clientId, {
            sessionId,
            createdAt: Date.now(),
            lastActivity: Date.now()
        });
        console.log(`Created new detection session for client ${clientId}: ${sessionId}`);
    }

    const session = clientSessions.get(clientId);
    session.lastActivity = Date.now();
    return session.sessionId;
}

function cleanupClientSessions() {
    const now = Date.now();
    const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes

    for (const [clientId, session] of clientSessions.entries()) {
        if (now - session.lastActivity > SESSION_TIMEOUT) {
            clientSessions.delete(clientId);
            console.log(`Removed inactive detection session for client ${clientId}: ${session.sessionId}`);
        }
    }
}

async function handleFaceRecognition(req, res) {
    const startTime = Date.now();

    try {
        if (!req.file) return res.status(400).json({ error: 'No face image.' });

        const knownUserId = req.body.userId || null;
        const clientId = req.body.clientId || req.headers['x-client-id'] || `client_${Date.now()}`;

        const sessionId = getOrCreateSessionId(clientId);

        console.log('Processing face recognition request:');
        console.log(`- Client ID: ${clientId}`);
        console.log(`- Session ID: ${sessionId}`);
        console.log(`- Known user ID: ${knownUserId || 'none (new detection)'}`);

        if (Math.random() < 0.1) {
            cleanupClientSessions();
        }

        const result = await recognizeFaceWithConfirmation(req.file.buffer, sessionId, knownUserId);
        const processingTime = Date.now() - startTime;

        if (result.error) return res.status(500).json({ error: result.error });

        let userStatus = 'existing';
        let responseMessage = '';

        if (result.isPreliminary) {
            responseMessage = `Collecting face data: ${result.detectionProgress}/${result.totalRequired}`;
            console.log(`PRELIMINARY DETECTION - ${responseMessage}`);
            console.log(`- Current detection: ${result.userId}`);
        } else if (result.isUncertain) {
            userStatus = 'uncertain';
            responseMessage = `Uncertain identity - no consensus reached (${result.detectionProgress}/${result.totalRequired} frames analyzed)`;
            console.log(`UNCERTAIN DETECTION - ${responseMessage}`);
        } else if (result.isConfirmed) {
            if (result.isNewUser) {
                userStatus = 'new_unknown';
                responseMessage = `NEW USER CONFIRMED with ${(result.consensusRatio * 100).toFixed(1)}% consensus`;
                console.log('NEW USER CONFIRMED!');
                console.log(`- Assigned ID: ${result.userId}`);
                console.log(`- Consensus ratio: ${(result.consensusRatio * 100).toFixed(1)}%`);
                console.log(`- Total users in system: ${result.totalUsers || 'unknown'}`);
            } else if (result.needsIdentification) {
                userStatus = 'existing_unknown';
                responseMessage = `EXISTING USER CONFIRMED - needs identification (${(result.consensusRatio * 100).toFixed(1)}% consensus)`;
                console.log('EXISTING USER WITHOUT NAME CONFIRMED!');
                console.log(`- User ID: ${result.userId}`);
                console.log(`- Consensus ratio: ${(result.consensusRatio * 100).toFixed(1)}%`);
                console.log(`- Needs identification: ${result.needsIdentification}`);
            } else {
                responseMessage = `IDENTIFIED USER CONFIRMED (${(result.consensusRatio * 100).toFixed(1)}% consensus)`;
                console.log('IDENTIFIED USER CONFIRMED!');
                console.log(`- User ID: ${result.userId}`);
                console.log(`- User name: ${result.userName}`);
                console.log(`- Total visits: ${result.totalVisits}`);
                console.log(`- Consensus ratio: ${(result.consensusRatio * 100).toFixed(1)}%`);
            }
        }

        if (messageIo && result.isConfirmed && (result.isNewUser || result.needsIdentification)) {
            console.log('Sending confirmed user notification to clients');
            messageIo.sockets.emit('user_detected', {
                userId: result.userId,
                userName: result.userName,
                needsIdentification: result.needsIdentification,
                isNewUser: result.isNewUser,
                consensusRatio: result.consensusRatio
            });
        }

        if (Math.random() < 0.05) {
            debugDatabase();
            console.log('Detection session stats:', getDetectionSessionStats());
        }

        const response = {
            userId: result.userId,
            userName: result.userName || 'unknown',
            isNewUser: result.isNewUser || false,
            needsIdentification: result.needsIdentification || false,
            userStatus: userStatus,
            processingTime: processingTime,
            timestamp: new Date().toISOString(),
            sessionId: sessionId,
            clientId: clientId,
            message: responseMessage
        };

        if (result.isPreliminary) {
            response.isPreliminary = true;
            response.detectionProgress = result.detectionProgress;
            response.totalRequired = result.totalRequired;
            response.message = responseMessage;
        } else if (result.isUncertain) {
            response.isUncertain = true;
            response.detectionProgress = result.detectionProgress;
            response.totalRequired = result.totalRequired;
            response.consensusRatio = result.consensusRatio;
            response.message = responseMessage;
        } else if (result.isConfirmed) {
            response.isConfirmed = true;
            response.consensusRatio = result.consensusRatio;
            response.confidence = result.distance ? (1 - Math.min(result.distance, 1)).toFixed(3) : null;
            response.message = responseMessage;
        }

        console.log('=== FACE RECOGNITION REQUEST END ===');
        res.json(response);

    } catch (error) {
        const processingTime = Date.now() - startTime;
        console.error('=== FACE RECOGNITION ERROR ===');
        console.error('Error details:', error);
        console.error('Stack trace:', error.stack);
        console.error(`Failed after: ${processingTime}ms`);
        console.error('==============================');

        res.status(500).json({
            error: 'Internal server error in face recognition.',
            details: process.env.NODE_ENV === 'development' ? error.message : undefined,
            processingTime: processingTime
        });
    }
}

function handleListUsers(req, res) {
    try {
        const users = listAllUsers();
        const sessionStats = getDetectionSessionStats();
        res.json({ users, total: users.length, detectionSessions: sessionStats });
    } catch (error) {
        console.error('Error listing all users:', error);
        res.status(500).json({ error: 'Internal server error in listing all users.' });
    }
}

function handleDebugDatabase(req, res) {
    try {
        debugDatabase();
        const users = listAllUsers();
        const sessionStats = getDetectionSessionStats();

        res.json({
            message: 'Database debug completed - check server logs',
            summary: {
                totalUsers: users.length,
                users: users.map(u => ({
                    userId: u.userId,
                    userName: u.userName,
                    visits: u.visits,
                    lastSeen: u.lastSeen,
                    descriptorSamples: u.descriptorSamples,
                    isTemporary: u.isTemporary
                })),
                detectionSessions: sessionStats,
                clientSessions: Array.from(clientSessions.entries()).map(([clientId, session]) => ({
                    clientId,
                    sessionId: session.sessionId,
                    createdAt: new Date(session.createdAt).toISOString(),
                    lastActivity: new Date(session.lastActivity).toISOString(),
                    age: Date.now() - session.createdAt
                }))
            }
        });
    } catch (error) {
        console.error('Error debugging database:', error);
        res.status(500).json({ error: 'Internal server error in debugging database.' });
    }
}

async function handleUpdateUserName(req, res) {
    try {
        const { userId, userName } = req.body;
        if (!userId || !userName) {
            return res.status(400).json({ error: 'Missing userId or userName in the request body.' });
        }
        const result = await updateUserName(userId, userName);

        if (result.success) {
            console.log(`User ${userId} updated with name ${userName}`);
            res.json({
                message: 'User name updated successfully',
                userId: userId,
                userName: userName,
                oldUserId: result.oldUserId
            });
        } else {
            res.status(404).json({ error: 'User not found or unable to update user name.' });
        }
    } catch (error) {
        console.error('Error updating user name:', error);
        res.status(500).json({ error: 'Internal server error in updating user name.' });
    }
}

function handleDetectionStats(req, res) {
    try {
        const sessionStats = getDetectionSessionStats();
        const clientSessionStats = Array.from(clientSessions.entries()).map(([clientId, session]) => ({
            clientId,
            sessionId: session.sessionId,
            age: Date.now() - session.createdAt,
            lastActivity: Date.now() - session.lastActivity
        }));

        res.json({
            success: true,
            detectionSessions: sessionStats,
            clientSessions: clientSessionStats,
            totalActiveSessions: sessionStats.activeSessions,
            totalClients: clientSessions.size,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Error getting detection stats:', error);
        res.status(500).json({ error: 'Internal server error getting detection stats.' });
    }
}

module.exports = {
    handleFaceRecognition,
    handleListUsers,
    handleDebugDatabase,
    handleUpdateUserName,
    handleDetectionStats,
    setMessageSocketRef,
    upload
};