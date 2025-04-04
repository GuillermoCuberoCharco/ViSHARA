const { Server } = require('socket.io');
const config = require('./environment.cjs');

function setupSocketIO(server) {

    const videoIo = new Server(server, {
        path: '/video-socket',
        cors: config.cors || {
            origin: '*',
            methods: ['GET', 'POST'],
            credentials: true
        },
        transports: ['websocket', 'polling'],
        pingTimeout: 60000,
        pingInterval: 25000,
        connectTimeout: 45000
    });

    const messageIo = new Server(server, {
        path: '/message-socket',
        cors: config.cors || {
            origin: '*',
            methods: ['GET', 'POST'],
            credentials: true
        },
        transports: ['polling', 'websocket']
    });

    const animationIo = new Server(server, {
        path: '/animation-socket',
        cors: config.cors || {
            origin: '*',
            methods: ['GET', 'POST'],
            credentials: true
        },
        transports: ['websocket']
    });

    return { videoIo, messageIo, animationIo };
}

module.exports = setupSocketIO;