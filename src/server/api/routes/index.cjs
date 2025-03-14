const express = require('express');
const synthesizeRoutes = require('./synthesize.cjs');

const router = express.Router();

function setupRoutes(messageIo) {
    const setupTranscribeRoutes = require('./transcribe.cjs');

    router.use('/synthesize', synthesizeRoutes);
    router.use('/transcribe', setupTranscribeRoutes(messageIo));

    return router;
}

module.exports = setupRoutes;