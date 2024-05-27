const express = require('express');
const multer = require('multer');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');

function startCameraService() {
  const app = express();
  const server = http.createServer(app);
  const io = socketIo(server);
  app.use(cors());

  const storage = multer.memoryStorage();
  const upload = multer({ storage: storage });

  app.post('/upload', upload.single('file'), (req, res) => {
    if (req.file) {
      const base64Data = req.file.buffer.toString('base64');
      io.emit('video_chunk', base64Data);
      res.status(200).send('File received and processed');
    } else {
      console.error('No file received');
      res.status(400).send('No file received');
    }
  });

  io.on('connection', (socket) => {
    console.log('A user connected');
    socket.on('disconnect', () => {
      console.log('User disconnected');
    });
  });

  server.listen(3000, () => {
    console.log('Server running on port 3000');
  });
}

module.exports = { startCameraService };
