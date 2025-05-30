const { Server } = require('socket.io');
const config = require('./environment.cjs');

function setupSocketIO(server) {
    console.log('Setting up Socket.IO with CORS configuration:', JSON.stringify(config.cors));
    const origins = Array.isArray(config.cors.origin) ? config.cors.origin : [config.cors.origin];

    if (!origins.includes('https://vi-shara.vercel.app')) {
        origins.push('https://vi-shara.vercel.app');
    }

    const corsConfig = {
        origin: origins,
        methods: config.cors.methods,
        credentials: config.cors.credentials,
        allowedHeaders: config.cors.allowedHeaders,
        exposedHeaders: config.cors.exposedHeaders || []
    };

    console.log('Final CORS configuration:', JSON.stringify(corsConfig));

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
        transports: ['websocket', 'polling'],
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