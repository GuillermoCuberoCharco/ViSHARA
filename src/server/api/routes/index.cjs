const express = require('express');
const setupSynthesizeRoutes = require('./synthesize.cjs');
const setupTranscribeRoutes = require('./transcribe.cjs');
const setupFaceRecognitionRoutes = require('./faceRecognition.cjs');
const setupConversationRoutes = require('./conversations.cjs');

const router = express.Router();

function setupRoutes() {

    router.use('/synthesize', setupSynthesizeRoutes());
    router.use('/transcribe', setupTranscribeRoutes());
    router.use('/recognize-face', setupFaceRecognitionRoutes());
    router.use('/conversations', setupConversationRoutes());


    router.get('/health', (req, res) => {
        res.json({
            success: true,
            service: 'SHARA API',
            status: 'healthy',
            version: '1.0.0',
            uptime: process.uptime(),
            endpoints: {
                synthesize: '/api/synthesize',
                transcribe: '/api/transcribe',
                faceRecognition: '/api/recognize-face',
                conversations: '/api/conversations'
            },
            timestamp: new Date().toISOString()
        });
    });

    return router;
}

module.exports = setupRoutes;