const multer = require('multer');

function startCameraService(app, io) {
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
}

module.exports = { startCameraService };
