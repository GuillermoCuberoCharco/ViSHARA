const express = require('express');
const synthesizeRoutes = require('./synthesize');

const router = express.Router();

function setupRoutes(messageIo) {
    const setupTranscribeRoutes = require('./transcribe');

    router.use('/synthesize', synthesizeRoutes);
    router.use('/transcribe', setupTranscribeRoutes(messageIo));

    return router;
}

module.exports = setupRoutes;