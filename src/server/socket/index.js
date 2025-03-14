const { setupMessageHandlers } = require('./handlers/messageHandler');
const { setupVideoHandlers } = require('./handlers/videoHandler');

function setupSockets(io) {
    const { messageIo, videoIo } = io;

    setupMessageHandlers(messageIo);

    const { videoSubscribers } = setupVideoHandlers(videoIo);

    return { videoSubscribers };
}

module.exports = setupSockets;