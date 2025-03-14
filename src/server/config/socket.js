const { Server } = require('socket.io');
const config = require('./environment');

function setupSocketIO(server) {

    const videoIo = new Server(server, {
        path: '/video-socket',
        cors: config.cors,
        transports: ['websocket']
    });

    const messageIo = new Server(server, {
        cors: config.cors,
        transports: ['polling', 'websocket']
    });

    return { videoIo, messageIo };
}

module.exports = setupSocketIO;