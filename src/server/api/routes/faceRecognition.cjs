const express = require('express');
const { handleBatchFaceRecognition, handleListUsers, handleDebugDatabase, handleUpdateUserName, handleDetectionStats, uploadBatch } = require('../controllers/faceRecognitionController.cjs');

const router = express.Router();

function setupFaceRecognitionRoutes() {
    router.post('/', uploadBatch.array('faces', 10), handleBatchFaceRecognition);
    router.get('/users', handleListUsers);
    router.get('/debug', handleDebugDatabase);
    router.put('/user/name', handleUpdateUserName);
    router.get('/detection-stats', handleDetectionStats);

    return router;
}

module.exports = setupFaceRecognitionRoutes;