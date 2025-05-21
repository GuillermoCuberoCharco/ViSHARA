const express = require('express');
const { handleFaceRecognition, listAllUsers } = require('../controllers/faceRecognitionController.cjs');

const router = express.Router();

function setupFaceRecognitionRoutes() {

    router.post('/', express.json({ limit: '1mb' }), handleFaceRecognition);
    router.get('/users', listAllUsers);

    return router;
}

module.exports = setupFaceRecognitionRoutes;