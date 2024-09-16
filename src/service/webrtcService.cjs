
const socketIo = require('socket.io');
const net = require('net');


function setupWebRTC(server) {
  const io = socketIo(server, {
    path: '/webrtc',
    cors: {
      origin: 'http://localhost:5173',
      methods: ['GET', 'POST'],
      credentials: true
    }
  });

  let pythonClient = null;

  const tcpServer = net.createServer((socket) => {
    console.log('TCP client connected');
    pythonClient = socket;

    socket.on('data', (data) => {
      console.log('Data received:', data.toString());
      io.emit('data', data.toString());
    });

    socket.on('end', () => {
      console.log('TCP client disconnected');
      pythonClient = null;
    });
  });

  tcpServer.listen(4000, () => {
    console.log('TCP server listening on port 4000');
  });

  io.on('connection', (socket) => {
    console.log('New WebRTC connection');

    socket.on('offer', (offer) => {
      console.log('Offer received:', offer);
      if (pythonClient) {
        pythonClient.write(offer + '\n');
        console.log('Offer sent to TCP client');
      } else {
        console.log('No TCP client connected');
      }
    });

    socket.on('ice-candidate', (candidate) => {
      console.log('Ice candidate received:', candidate);
      if (pythonClient) {
        pythonClient.write(JSON.stringify({ type: 'ice-candidate', candidate: candidate }) + '\n');
        console.log('Ice candidate sent to TCP client');
      }
      console.log('No TCP client connected');
    });

    socket.on('disconnect', () => {
      console.log('WebRTC connection disconnected');
    });
  });

  return io;
}

module.exports = { setupWebRTC };