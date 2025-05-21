const express = require('express');
const { handleFaceRecognition, handleListUsers } = require('../controllers/faceRecognitionController.cjs');

const router = express.Router();

function setupFaceRecognitionRoutes() {
    router.post('/', express.json({ limit: '1mb' }), handleFaceRecognition);
    router.get('/users', handleListUsers);

    return router;
}

module.exports = setupFaceRecognitionRoutes;