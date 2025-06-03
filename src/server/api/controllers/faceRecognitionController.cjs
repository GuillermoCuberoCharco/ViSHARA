const { recognizeFaceWithBatch, listAllUsers, debugDatabase, updateUserName, getDetectionSessionStats } = require('../../services/faceRecognitionService.cjs');
const multer = require('multer');

const storage = multer.memoryStorage();

const uploadBatch = multer({
    storage: storage,
    limits: {
        fileSize: 10 * 1024 * 1024, // 10MB por archivo
        fieldSize: 10 * 1024 * 1024,
        files: 10 // Máximo 10 archivos por lote
    },
    fileFilter: (req, file, cb) => {

        if (!file.mimetype.startsWith('image/')) {
            console.error('Invalid file type in batch:', file.mimetype);
            return cb(new Error('Only image files are allowed'), false);
        }
        cb(null, true);
    }
});

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

async function handleBatchFaceRecognition(req, res) {
    const startTime = Date.now();
    let processingStep = 'initialization';

    try {
        console.log('=== BATCH FACE RECOGNITION REQUEST START ===');

        processingStep = 'files_validation';
        if (!req.files || !Array.isArray(req.files) || req.files.length === 0) {
            console.error('No files received in batch request');
            return res.status(400).json({ error: 'No face images provided in batch.' });
        }

        console.log(`Batch received: ${req.files.length} files`);
        req.files.forEach((file, index) => {
            console.log(`File ${index + 1}:`, {
                fieldname: file.fieldname,
                originalname: file.originalname,
                mimetype: file.mimetype,
                size: file.size
            });
        });

        for (let i = 0; i < req.files.length; i++) {
            const file = req.files[i];
            if (!file.buffer || file.buffer.length === 0) {
                console.error(`File ${i + 1} buffer is empty or invalid`);
                return res.status(400).json({ error: `Invalid or empty image file at position ${i + 1}.` });
            }
        }

        processingStep = 'parameter_extraction';
        const knownUserId = req.body.userId || null;
        const clientId = req.body.clientId || req.headers['x-client-id'] || `client_${Date.now()}`;
        const sessionId = req.body.sessionId || getOrCreateSessionId(clientId);

        console.log('Processing parameters:', {
            knownUserId,
            clientId,
            sessionId,
            filesCount: req.files.length,
            bodyKeys: Object.keys(req.body)
        });

        processingStep = 'session_cleanup';
        if (Math.random() < 0.1) {
            cleanupClientSessions();
        }

        processingStep = 'batch_face_recognition';
        console.log('Calling recognizeFaceWithBatch...');

        const faceBuffers = req.files.map(file => file.buffer);

        const result = await recognizeFaceWithBatch(faceBuffers, sessionId, knownUserId);

        console.log('Batch recognition result received:', {
            userId: result.userId,
            isConfirmed: result.isConfirmed,
            isUncertain: result.isUncertain,
            consensusRatio: result.consensusRatio,
            isNewUser: result.isNewUser
        });

        const processingTime = Date.now() - startTime;

        if (result.error) {
            console.error('Batch face recognition service returned error:', result.error);
            return res.status(500).json({ error: result.error });
        }

        processingStep = 'response_preparation';
        let userStatus = 'existing';
        let responseMessage = '';

        if (result.isUncertain) {
            userStatus = 'uncertain';
            responseMessage = `Uncertain identity - no consensus reached (${(result.consensusRatio * 100).toFixed(1)}% agreement)`;
            console.log(`BATCH UNCERTAIN - ${responseMessage}`);
        } else if (result.isConfirmed) {
            if (result.isNewUser) {
                userStatus = 'new_unknown';
                responseMessage = `NEW USER CONFIRMED with ${(result.consensusRatio * 100).toFixed(1)}% consensus from ${req.files.length} images`;
                console.log('BATCH NEW USER CONFIRMED!');
                console.log(`- Assigned ID: ${result.userId}`);
                console.log(`- Consensus ratio: ${(result.consensusRatio * 100).toFixed(1)}%`);
            } else if (result.needsIdentification) {
                userStatus = 'existing_unknown';
                responseMessage = `EXISTING USER CONFIRMED - needs identification (${(result.consensusRatio * 100).toFixed(1)}% consensus)`;
                console.log('BATCH EXISTING USER WITHOUT NAME CONFIRMED!');
                console.log(`- User ID: ${result.userId}`);
                console.log(`- Consensus ratio: ${(result.consensusRatio * 100).toFixed(1)}%`);
            } else {
                responseMessage = `IDENTIFIED USER CONFIRMED (${(result.consensusRatio * 100).toFixed(1)}% consensus)`;
                console.log('BATCH IDENTIFIED USER CONFIRMED!');
                console.log(`- User ID: ${result.userId}`);
                console.log(`- User name: ${result.userName}`);
                console.log(`- Total visits: ${result.totalVisits}`);
                console.log(`- Consensus ratio: ${(result.consensusRatio * 100).toFixed(1)}%`);
            }
        }

        processingStep = 'socket_notification';
        if (messageIo && result.isConfirmed && (result.isNewUser || result.needsIdentification)) {
            try {
                console.log('Sending batch confirmed user notification to clients');
                messageIo.sockets.emit('user_detected', {
                    userId: result.userId,
                    userName: result.userName,
                    needsIdentification: result.needsIdentification,
                    isNewUser: result.isNewUser,
                    consensusRatio: result.consensusRatio
                });
            } catch (socketError) {
                console.error('Error sending socket notification:', socketError);
            }
        }

        processingStep = 'response_construction';
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
            message: responseMessage,
            batchSize: req.files.length
        };

        if (result.isUncertain) {
            response.isUncertain = true;
            response.consensusRatio = result.consensusRatio;
            response.detectionProgress = req.files.length;
            response.totalRequired = req.files.length;
        } else if (result.isConfirmed) {
            response.isConfirmed = true;
            response.consensusRatio = result.consensusRatio;
            response.confidence = result.confidence ? (result.confidence * 100).toFixed(1) + '%' : null;
            response.avgDistance = result.distance ? result.distance.toFixed(3) : null;
        }

        console.log('=== BATCH FACE RECOGNITION SUCCESS ===');
        console.log(`Processing time: ${processingTime}ms for ${req.files.length} images`);
        res.json(response);

    } catch (error) {
        const processingTime = Date.now() - startTime;
        console.error('=== BATCH FACE RECOGNITION ERROR ===');
        console.error(`Error at step: ${processingStep}`);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            name: error.name
        });
        console.error(`Failed after: ${processingTime}ms`);
        console.error('Request info:', {
            hasFiles: !!req.files,
            filesCount: req.files?.length || 0,
            bodyKeys: Object.keys(req.body || {}),
            headers: req.headers
        });

        if (!res.headersSent) {
            res.status(500).json({
                error: 'Internal server error in batch face recognition.',
                step: processingStep,
                details: process.env.NODE_ENV === 'development' ? error.message : 'Please check server logs',
                processingTime: processingTime,
                timestamp: new Date().toISOString()
            });
        }
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
    handleBatchFaceRecognition,
    handleListUsers,
    handleDebugDatabase,
    handleUpdateUserName,
    handleDetectionStats,
    setMessageSocketRef,
    uploadBatch
};