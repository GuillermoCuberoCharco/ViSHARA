const { recogniceFace, listAllUsers, debugDatabase } = require('../../services/faceRecognitionService.cjs');
const multer = require('multer');

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

async function handleFaceRecognition(req, res) {
    const startTime = Date.now();

    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No face image.' });
        }

        const knownUserId = req.body.userId || null;
        const imageSize = req.file.buffer.length;

        console.log('Processing face recognition request:');
        console.log(`- Image size: ${imageSize} bytes`);
        console.log(`- Known user ID: ${knownUserId || 'none (new detection)'}`);
        console.log(`- MIME type: ${req.file.mimetype}`);

        const result = await recogniceFace(req.file.buffer, knownUserId);
        const processingTime = Date.now() - startTime;

        if (result.error) {
            return res.status(500).json({ error: result.error });
        }

        if (result.isNewUser) {
            console.log('NEW USER DETECTED!');
            console.log(`- Assigned ID: ${result.userId}`);
            console.log(`- Total users in system: ${result.totalUsers || 'unknown'}`);
        } else {
            console.log('EXISTING USER RECOGNIZED!');
            console.log(`- User ID: ${result.userId}`);
            console.log(`- Distance: ${result.distance ? result.distance.toFixed(4) : 'unknown'}`);
            console.log(`- Total visits: ${result.totalVisits || 'unknown'}`);
        }

        if (Math.random() < 0.1) {
            debugDatabase();
        }

        res.json({
            userId: result.userId,
            isNewUser: result.isNewUser,
            confidence: result.distance ? (1 - Math.min(result.distance, 1)).toFixed(3) : null,
            processingTime: processingTime,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        const processingTime = Date.now() - startTime;
        console.error('Error processing face recognition:', error);
        console.log('Failed affter:', processingTime, 'ms');
        res.status(500).json({ error: 'Internal server error in face recognition.' });
    }
}

function handleListUsers(req, res) {
    try {
        const users = listAllUsers();
        res.json({ users, total: users.length });
    } catch (error) {
        console.error('Error listing all users:', error);
        res.status(500).json({ error: 'Internal server error in listing all users.' });
    }
}

function handleDebugDatabase(req, res) {
    try {
        debugDatabase();
        const users = listAllUsers();
        res.json({
            message: 'Database debug completed - check server logs',
            summary: {
                totalUsers: users.length,
                users: users.map(u => ({
                    userId: u.userId,
                    visits: u.visits,
                    lastSeen: u.lastSeen,
                    descriptorSamples: u.descriptorSamples
                }))
            }
        });
    } catch (error) {
        console.error('Error debugging database:', error);
        res.status(500).json({ error: 'Internal server error in debugging database.' });
    }
}

module.exports = {
    handleFaceRecognition,
    handleListUsers,
    handleDebugDatabase,
    upload
};