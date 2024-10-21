const express = require('express');
const http = require('http');
const { Server } = require("socket.io");
const WebSocket = require('ws');

const app = express();
const server = http.createServer(app);

// Middleware para CORS
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});


const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  },
  transports: ['websocket']
});

const clients = new Set();
let framesReceived = 0;
let framesForwarded = 0;

// Socket.IO handling
io.on('connection', (socket) => {
  console.log('A Socket.IO client connected');

  socket.on('register', (clientType) => {
    console.log(`Socket.IO client registered: ${clientType}`);
    clients.add({ socket, type: clientType, protocol: 'socketio' });
  });

  socket.on('video-frame', (frame) => {
    for (const client of clients) {
      if (client.type === 'python' && client.protocol === 'ws') {
        client.socket.send(JSON.stringify({ type: 'video', frame }));
        framesForwarded++;
      } else if (client.type === 'python' && client.protocol === 'socketio') {
        client.socket.emit('video', { type: 'video', frame });
        framesForwarded++;
      }
    }
    if (framesReceived % 100 === 0) {
      console.log(`Frames received: ${framesReceived}, frames forwarded: ${framesForwarded}`);
    }
  });

  socket.on('disconnect', () => {
    console.log('Socket.IO client disconnected');
    clients.forEach(client => {
      if (client.socket === socket) {
        clients.delete(client);
      }
    });
  });
});

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
        if (framesReceived % 100 === 0) {
          console.log(`Received: ${framesReceived}`);
        }
        for (const client of clients) {
          if (client.type === 'python' && client.protocol === 'ws') {
            client.socket.send(JSON.stringify({ type: 'video', frame: data.frame }));
            framesForwarded++;
          } else if (client.type === 'python' && client.protocol === 'socketio') {
            client.socket.emit('video', { type: 'video', frame: data.frame });
            framesForwarded++;
          }
        }
        if (framesReceived % 100 === 0) {
          console.log(`Forwarded: ${framesForwarded}`);
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

  if (pathname === '/socket') {
    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request);
    });
  } else if (pathname.startsWith('/socket.io/')) {
    socket.destroy();
  } else {
    socket.destroy();
    console.log('Invalid upgrade request, socket destroyed');
  }
});


app.get('/', (req, res) => {
  res.send('Server is running');
});

server.listen(8081, () => {
  console.log('Server is running on port 8081');
});