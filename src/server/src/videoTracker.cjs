const WebSocket = require('ws');


function startVideoService(server) {
  const clients = new Set();
  let framesReceived = 0;
  let framesForwarded = 0;

  // WebSocket handling
  const wss = new WebSocket.Server({ noServer: true });

  wss.on('connection', (ws) => {
    console.log('A WebSocket client connected');

    ws.on('message', (message) => {
      try {
        const data = JSON.parse(message);
        if (data.type === 'register') {
          console.log(`WebSocket client registered: ${data.client}`);
          clients.add({ socket: ws, type: data.client, protocol: 'ws' });
        } else if (data.type === 'video-frame') {
          framesReceived++;
          for (const client of clients) {
            if (client.type === 'python' && client.protocol === 'ws') {
              client.socket.send(JSON.stringify({ type: 'video', frame: data.frame }));
              framesForwarded++;
            } else if (client.type === 'python' && client.protocol === 'socketio') {
              client.socket.emit('video', { type: 'video', frame: data.frame });
              framesForwarded++;
            }
          }
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    });

    ws.on('close', () => {
      console.log('WebSocket client disconnected');
      clients.forEach(client => {
        if (client.socket === ws) {
          clients.delete(client);
        }
      });
    });
  });

  server.on('upgrade', (request, socket, head) => {
    const pathname = request.url;
    console.log('Upgrade request received for:', pathname);

    if (pathname === '/video-socket') {
      wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit('connection', ws, request);
      });
    }
  });
}

module.exports = { startVideoService };