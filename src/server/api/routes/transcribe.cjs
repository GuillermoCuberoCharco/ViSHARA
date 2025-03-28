const express = require('express');

const router = express.Router();

function setupTranscribeRoutes(messageIo) {
    const { handleTranscribe } = require('../controllers/transcribeController.cjs');

    router.post('/', (req, res) => handleTranscribe(req, res, messageIo));

    return router;
}

module.exports = setupTranscribeRoutes;