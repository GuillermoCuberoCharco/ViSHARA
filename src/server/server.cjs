const http = require('http');
const setupExpress = require('./config/app.cjs');
const setupSocketIO = require('./config/socket.cjs');
const setupRoutes = require('./api/routes/index.cjs');
const setupSockets = require('./socket/index.cjs');
const faceService = require('./services/faceService.cjs');
const { setMessageSocketRef } = require('./api/controllers/faceRecognitionController.cjs');
const { initConversationService, cleanupOldConversations } = require('./services/conversationService.cjs');
const config = require('./config/environment.cjs');

// Initialize Express app
const app = setupExpress();
console.log('Express app initialized');

// Create HTTP server
const server = http.createServer(app);
console.log('HTTP server created');

// Initialize Socket.IO
const io = setupSocketIO(server);
console.log('Socket.IO initialized');

// Set the message socket reference
setMessageSocketRef(io);
console.log('Message socket reference set');

// Configure API routes
app.use('/api', setupRoutes());
console.log('API routes configured');

// Initialize services
faceService.startCameraService(app, io.videoIo);
console.log('Camera service initialized');

// Initialize conversation service
async function initializeConversationHistory() {
    try {
        await initConversationService();
        console.log('Conversation service initialized');
        await cleanupOldConversations(90);
        console.log('Old conversations cleanup completed');
    } catch (error) {
        console.error('Error initializing conversation service: ', error);
    }
}

// Configure sockets
setupSockets(io);
console.log('Sockets configured');

initializeConversationHistory();

// Start the server
server.listen(config.port, () => {
    console.log(`Server is running on port ${config.port}`);
    console.log(`Video Socket.IO service available at /video-socket`);
    console.log(`Message Socket.IO service available at /message-socket`);
    console.log(`Animation Socket.IO service available at /animation-socket`);
    console.log(`Face detection service available at /upload`);
    console.log(`API endpoints available at /api/*`);
    console.log(`===================================`);
});

// Handle unhandled promise rejections
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('SIGINT', async () => {
    console.log('Received SIGINT, shutting down gracefully...');

    try {
        // Save conversations before closing up
        const { saveConversationsToFile } = require('./services/conversationService.cjs');
        await saveConversationsToFile();
        console.log('Conversations saved before shutdown');
    } catch (error) {
        console.error('Error saving conversations during shutdown:', error);
    }

    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, shutting down gracefully...');

    try {
        const { saveConversationsToFile } = require('./services/conversationService.cjs');
        await saveConversationsToFile();
        console.log('Conversations saved before shutdown');
    } catch (error) {
        console.error('Error saving conversations during shutdown:', error);
    }

    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});