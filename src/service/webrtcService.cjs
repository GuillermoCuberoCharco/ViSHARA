function setupWebRTC(io) {
  const webrtcNamespace = io.of('/webrtc');

  let pythonClients = new Set();
  let webClients = new Set();
  let pendingOffers = [];

  webrtcNamespace.on('connection', (socket) => {
    console.log('New WebRTC connection: ', socket.id);

    // Identify clients
    socket.on('register', (clientType) => {
      console.log(`Client registered as ${clientType}:`, socket.id);
      if (clientType === 'python') {
        pythonClients.add(socket);
        if (pendingOffers.length > 0) {
          pendingOffers.forEach((offer) => {
            socket.emit('offer', offer);
          });
          pendingOffers = [];
        }
      } else if (clientType === 'web') {
        webClients.add(socket);
      }
    });

    socket.on('offer', (offer) => {
      console.log('Offer received:', offer);
      if (pythonClients.size > 0) {
        console.log('Forwarding offer to Python client');
        pythonClients.forEach((client) => client.emit('offer', offer));
      } else {
        console.log('No Python client connected to receive offer');
        pendingOffers.push(offer);
      }
    });

    socket.on('answer', (answer) => {
      console.log('Answer received from: ', socket.id);
      if (webClients.size > 0) {
        console.log('Forwarding answer to Web client');
        webClients.forEach((client) => client.emit('answer', answer));
      } else {
        console.log('No Web client connected to receive answer');
      }
    });

    socket.on('ice-candidate', (candidate) => {
      console.log('ICE candidate received: ', candidate);
      if (pythonClients.has(socket)) {
        webClients.forEach((client) => client.emit('ice-candidate', candidate));
      } else if (webClients.has(socket)) {
        pythonClients.forEach((client) => client.emit('ice-candidate', candidate));
      }
      console.log('ICE candidate forwarded');
    });

    socket.on('disconnect', (reason) => {
      console.log(`Client ${socket.id} disconnected. Reason: ${reason}`);
      pythonClients.delete(socket);
      webClients.delete(socket);
    });


  });

  return webrtcNamespace;
}

module.exports = { setupWebRTC };