import axios from 'axios';
const express = require('express');
const app = express();
const bodyParser = require('body-parser');
const cors = require("cors");
const wrtc = require('wrtc');

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

const peers = new Map();

const upload = async (req, res) => {
  console.log('Received SDP');
  const sdp = req.body.sdp;

  const configuration = {
    iceServers: [
      {
        urls: 'http://localhost:3478'
      }
    ]
  };
  const peer = new wrtc.RTCPeerConnection(configuration);

  peers.set(sdp, peer);

  peer.onicecandidate = ({ candidate }) => {
    if (candidate) {
      axios.post('http://localhost:8082/candidates', { candidate: candidate })
        .then(() => console.log('ICE candidate sent to server.'))
        .catch(error => console.error('Error sending ICE candidate to server:', error));
    }
  };

  peer.onconnectionstatechange = () => {
    if (peer.connectionState === 'disconnected' || peer.connectionState === 'failed' || peer.connectionState === 'closed') {
      console.log('WebRTC connection closed');
      peers.delete(sdp);
    }
  };

  await peer.setRemoteDescription(sdp);
  const answer = await peer.createAnswer();
  await peer.setLocalDescription(answer);

  res.json({ sdp: peer.localDescription });
};

module.exports = upload;