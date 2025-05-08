function setupAnimationHandlers(io) {
    io.on('connection', (socket) => {
        console.log('New animation connection: ', socket.id);
        socket.on('register_animation', (data) => {
            console.log('Client registered:', data.client, socket.id);
            if (data.client === 'animation') {
                socket.emit('registration_success', { status: 'ok' });
            }
        });
    });
}

module.exports = { setupAnimationHandlers };