const express = require('express');
const { handleSynthesize } = require('../controllers/synthesizeControllers.cjs');

const router = express.Router();

function setupSynthesizeRoutes() {
    router.post('/', handleSynthesize);
    return router;
}

module.exports = setupSynthesizeRoutes;