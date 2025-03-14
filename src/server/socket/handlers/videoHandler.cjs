function setupVideoHandlers(io) {
    const videoSubscribers = new Set();

    io.on('connection', (socket) => {
        console.log('New video connection');
        socket.on('subscribe_video', () => {
            videoSubscribers.add(socket.id);
            console.log('New subscriber:', socket.id);
        });
        socket.on('unsubscribe_video', () => {
            videoSubscribers.delete(socket.id);
            console.log('Subscriber disconnected:', socket.id);
        });
        socket.on('disconnect', () => {
            videoSubscribers.delete(socket.id);
            console.log('Subscriber disconnected:', socket.id);
        });
    });

    return { videoSubscribers };
}

module.exports = { setupVideoHandlers }