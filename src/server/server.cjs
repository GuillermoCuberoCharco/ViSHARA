const http = require('http');
const setupExpress = require('./config/app.cjs');
const setupSocketIO = require('./config/socket.cjs');
const setupRoutes = require('./api/routes/index.cjs');
const setupSockets = require('./socket/index.cjs');
const { startCameraService } = require('./services/faceService.cjs');
const { startVideoService } = require('./services/videoService.cjs');
const config = require('./config/environment.cjs');

// Initialize Express app
const app = setupExpress();

// Create HTTP server
const server = http.createServer(app);

// Initialize Socket.IO
const io = setupSocketIO(server);

// Configure API routes
app.use('/api', setupRoutes(io.messageIo));

// Initialize services
startCameraService(app, io.videoIo);
startVideoService(server);

// Configure sockets
setupSockets(io);

// Start the server
server.listen(config.port, () => {
    console.log(`Server is running on port ${config.port}`);
    console.log(`Video WebSocket service available at /video-socket`);
    console.log(`Face detection service available at /upload`);
    console.log(`API endpoints available at /api/*`);
});

// Handle unhandled promise rejections
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});