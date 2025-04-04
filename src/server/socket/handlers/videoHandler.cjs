function setupVideoHandlers(io) {
    const videoSubscribers = new Set();

    io.on('connection', (socket) => {
        console.log('New video connection: ', socket.id);

        socket.on('register', (data) => {
            console.log('Client registered:', data.client, socket.id);
            if (data.client === 'web') {
                socket.emit('registration_success', { status: 'ok' });
            }
        });
        socket.on('video_frame', (data) => {
            if (videoSubscribers.size > 0) {
                for (const subscriberId of videoSubscribers) {
                    if (subscriberId !== socket.id) {
                        io.to(subscriberId).emit('video-frame', {
                            type: 'video-frame',
                            frame: data.frame,
                        });
                    }
                }
            }
        });
        socket.on('subscribe_video', () => {
            videoSubscribers.add(socket.id);
            console.log('New python subscriber:', socket.id);
            socket.emit('subcription_success', { status: 'ok' });
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