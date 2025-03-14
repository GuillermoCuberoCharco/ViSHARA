const { setupMessageHandlers } = require('./handlers/messageHandler.cjs');
const { setupVideoHandlers } = require('./handlers/videoHandler.cjs');

function setupSockets(io) {
    const { messageIo, videoIo } = io;

    setupMessageHandlers(messageIo);

    const { videoSubscribers } = setupVideoHandlers(videoIo);

    return { videoSubscribers };
}

module.exports = setupSockets;