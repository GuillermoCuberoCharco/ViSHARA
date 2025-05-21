const { recogniceFace, listAllUsers } = require('../../services/faceRecognitionService.cjs');

async function handleFaceRecognition(req, res) {
    try {
        const { faceDescriptor, userId } = req.body;

        if (!faceDescriptor || !Array.isArray(faceDescriptor)) {
            return res.status(400).json({ error: 'Invalid face descriptor.' });
        }

        const result = await recogniceFace(faceDescriptor, userId);
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
    handleListUsers
};