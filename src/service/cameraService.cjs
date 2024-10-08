const multer = require('multer');

function startCameraService(app, io) {
  const storage = multer.memoryStorage();
  const upload = multer({ storage: storage });
  const videoSubscribers = new Set();

  app.post('/upload', upload.single('file'), (req, res) => {
    if (req.file) {
      const base64Data = req.file.buffer.toString('base64');
      for (let socketIo of videoSubscribers) {
        io.to(socketIo).emit('video_chunk', base64Data);
      }
      res.status(200).send('File received and processed');
    } else {
      console.error('No file received');
      res.status(400).send('No file received');
    }
  });

  io.on('connection', (socket) => {
    console.log('A user connected');

    socket.on('subscribe_video', () => {
      videoSubscribers.add(socket.id);
      console.log(`User ${socket.id} subscribed to video`);
    });

    socket.on('unsubscribe_video', () => {
      videoSubscribers.delete(socket.id);
      console.log(`User ${socket.id} unsubscribed from video`);
    });

    socket.on('disconnect', () => {
      videoSubscribers.delete(socket.id);
      console.log('User disconnected');
    });
  });
}

module.exports = { startCameraService };
