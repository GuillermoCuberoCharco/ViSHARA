const express = require('express');
const { handleFaceRecognition, handleListUsers, handleDebugDatabase, upload } = require('../controllers/faceRecognitionController.cjs');

const router = express.Router();

function setupFaceRecognitionRoutes() {
    router.post('/', upload.single('face'), handleFaceRecognition);
    router.get('/users', handleListUsers);
    router.get('/debug', handleDebugDatabase);

    return router;
}

module.exports = setupFaceRecognitionRoutes;