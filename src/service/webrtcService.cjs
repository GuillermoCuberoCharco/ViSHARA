const socketIo = require('socket.io');

function setupWebRTC(server) {
  const io = socketIo(server, {
    path: '/webrtc',
    cors: {
      origin: 'http://localhost:5173',
      methods: ['GET', 'POST'],
      credentials: true
    }
  });

  io.on('connection', (socket) => {
    console.log('New WebRTC connection');

    socket.on('offer', async (offer) => {
      console.log('Received offer, resending');
      await socket.broadcast.emit('offer', offer);
    });

    socket.on('answer', async (answer) => {
      console.log('Received answer, resending');
      await socket.broadcast.emit('answer', answer);
    });

    socket.on('ice-candidate', async (candidate) => {
      console.log('Received ICE candidate, resending');
      await socket.broadcast.emit('ice-candidate', candidate);
    });

    socket.on('disconnect', () => {
      console.log('WebRTC connection disconnected');
    });
  });

  return io;
}

module.exports = { setupWebRTC };