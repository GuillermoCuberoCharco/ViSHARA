const { Server } = require('socket.io');
const config = require('./environment.cjs');

function setupSocketIO(server) {
    console.log('Setting up Socket.IO with CORS configuration:', config.cors);

    const corsConfig = {
        origin: '*',
        methods: config.cors.methods || ['GET', 'POST', 'OPTIONS'],
        credentials: config.cors.credentials || true,
        allowedHeaders: config.cors.allowedHeaders || ['Content-Type', 'Authorization']
    };

    const videoIo = new Server(server, {
        path: '/video-socket',
        cors: corsConfig,
        transports: ['websocket', 'polling'],
        pingTimeout: 60000,
        pingInterval: 25000,
        connectTimeout: 45000
    });

    const messageIo = new Server(server, {
        path: '/message-socket',
        cors: corsConfig,
        transports: ['polling', 'websocket'],
        pingTimeout: 60000,
        pingInterval: 25000,
        connectTimeout: 45000
    });

    const animationIo = new Server(server, {
        path: '/animation-socket',
        cors: corsConfig,
        transports: ['websocket']
    });

    return { videoIo, messageIo, animationIo };
}

module.exports = setupSocketIO;