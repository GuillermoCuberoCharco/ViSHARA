const express = require('express');
const { handleFaceRecognition, handleListUsers, handleDebugDatabase, handleUpdateUserName, handleDetectionStats, upload } = require('../controllers/faceRecognitionController.cjs');

const router = express.Router();

function setupFaceRecognitionRoutes() {
    router.post('/', upload.single('face'), handleFaceRecognition);
    router.get('/users', handleListUsers);
    router.get('/debug', handleDebugDatabase);
    router.put('/user/name', handleUpdateUserName);
    router.get('/detection-stats', handleDetectionStats);

    return router;
}

module.exports = setupFaceRecognitionRoutes;