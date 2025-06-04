const express = require('express');
const { handleBatchFaceRecognition, uploadBatch } = require('../controllers/faceRecognitionController.cjs');

const router = express.Router();

function setupFaceRecognitionRoutes() {
    router.post('/', uploadBatch.array('faces', 10), handleBatchFaceRecognition);

    return router;
}

module.exports = setupFaceRecognitionRoutes;