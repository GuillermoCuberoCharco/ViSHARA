const express = require('express');
const { handleTranscribe } = require('../controllers/transcribeController.cjs');

const router = express.Router();

function setupTranscribeRoutes() {
    router.post('/', handleTranscribe);
    return router;
}

module.exports = setupTranscribeRoutes;