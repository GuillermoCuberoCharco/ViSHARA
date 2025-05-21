const express = require('express');
const synthesizeRoutes = require('./synthesize.cjs');
const setupTranscribeRoutes = require('./transcribe.cjs');
const setupFaceRecognitionRoutes = require('./faceRecognition.cjs');

const router = express.Router();

function setupRoutes() {

    router.use('/synthesize', synthesizeRoutes);
    router.use('/transcribe', setupTranscribeRoutes());
    router.use('/recognize-face', setupFaceRecognitionRoutes());

    return router;
}

module.exports = setupRoutes;