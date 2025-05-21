const { recogniceFace, listAllUsers } = require('../../services/faceRecognitionService.cjs');
const multer = require('multer');

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

async function handleFaceRecognition(req, res) {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No face image.' });
        }

        const knownUserId = req.body.userId || null;

        const result = await recogniceFace(req.file.buffer, knownUserId);
        if (result.error) {
            return res.status(500).json({ error: result.error });
        }

        if (result.isNewUser) {
            console.log(`NEW USER DETECTED! ID: ${result.userId}`)
        } else {
            console.log(`USER RECOGNIZED! ID: ${result.userId}`)
        }

        res.json(result);
    } catch (error) {
        console.error('Error processing face recognition:', error);
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

module.exports = {
    handleFaceRecognition,
    handleListUsers,
    upload
};