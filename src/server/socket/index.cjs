const { setupMessageHandlers } = require('./handlers/messageHandler.cjs');
const { setupVideoHandlers } = require('./handlers/videoHandler.cjs');
const { setupAnimationHandlers } = require('./handlers/animationHandler.cjs');

function setupSockets(io) {
    const { messageIo, videoIo, animationIo } = io;

    setupMessageHandlers(messageIo);
    setupAnimationHandlers(animationIo);

    const { videoSubscribers } = setupVideoHandlers(videoIo);

    return { videoSubscribers };
}

module.exports = setupSockets;