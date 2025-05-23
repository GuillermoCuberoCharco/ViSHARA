const { recogniceFace, listAllUsers, debugDatabase, updateUserName } = require('../../services/faceRecognitionService.cjs');
const multer = require('multer');

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

let messageIo = null;
function setMessageSocketRef(io) {
    messageIo = io.messageIo;
}

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

        let userStatus = 'existing';

        if (result.isNewUser) {
            userStatus = 'new_unknown';
            console.log('NEW USER DETECTED!');
            console.log(`- Assigned ID: ${result.userId}`);
            console.log(`- Total users in system: ${result.totalUsers || 'unknown'}`);
        } else if (result.needsIdentification) {
            userStatus = 'existing_unknown';
            console.log('EXISTING USER WITHOUT NAME RECOGNIZED!');
            console.log(`- User ID: ${result.userId}`);
            console.log(`- Needs identification: ${result.needsIdentification}`);
        } else {
            console.log('IDENTIFIED USER RECOGNIZED!');
            console.log(`- User ID: ${result.userId}`);
            console.log(`- User name: ${result.userName}`);
            console.log(`- Total visits: ${result.totalVisits}`);
        }

        if (messageIo && (result.isNewUser || result.needsIdentification)) {
            console.log('Sending new user notification to clients');
            messageIo.emit('user_detected', {
                userId: result.userId,
                userName: result.userName,
                needsIdentification: result.needsIdentification,
                isNewUser: result.isNewUser
            });
        }

        if (Math.random() < 0.1) {
            debugDatabase();
        }

        res.json({
            userId: result.userId,
            userName: result.userName,
            isNewUser: result.isNewUser,
            needsIdentification: result.needsIdentification,
            userStatus: userStatus,
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
                    userName: u.userName,
                    visits: u.visits,
                    lastSeen: u.lastSeen,
                    descriptorSamples: u.descriptorSamples,
                    isTemporary: u.isTemporary
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

module.exports = {
    handleFaceRecognition,
    handleListUsers,
    handleDebugDatabase,
    handleUpdateUserName,
    setMessageSocketRef,
    upload
};