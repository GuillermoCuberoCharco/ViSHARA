const express = require('express');
const { handleFaceRecognition, handleListUsers, upload } = require('../controllers/faceRecognitionController.cjs');

const router = express.Router();

function setupFaceRecognitionRoutes() {
    router.post('/', upload.single('face'), handleFaceRecognition);
    router.get('/users', handleListUsers);

    return router;
}

module.exports = setupFaceRecognitionRoutes;