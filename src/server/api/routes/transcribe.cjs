const express = require('express');

const router = express.Router();

function setupTranscribeRoutes() {
    const { handleTranscribe } = require('../controllers/transcribeController.cjs');

    router.post('/', (req, res) => handleTranscribe(req, res));

    return router;
}

module.exports = setupTranscribeRoutes;