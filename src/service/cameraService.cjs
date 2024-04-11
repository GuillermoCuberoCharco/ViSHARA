const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8082 });
const { RTCPeerConnection } = require('wrtc');

const desktopAppWs = new WebSocket('ws://localhost:8083');

wss.on('connection', ws => {
  const pc = new RTCPeerConnection();

  pc.ontrack = event => {
    desktopAppWs.send(JSON.stringify({ track: event.track }));
    console.log('Received video track');
  };

  ws.on('message', message => {
    const data = JSON.parse(message);

    if (data.track) {
      pc.addTrack(data.track);
    }

    if (data.candidate) {
      pc.addIceCandidate(data.candidate);
    }
  });

  ws.on('close', () => {
    pc.close();
  });
});