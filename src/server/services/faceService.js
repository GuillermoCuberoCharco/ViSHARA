const multer = require('multer');

function startCameraService(app, io) {
    const storage = multer.memoryStorage();
    const upload = multer({ storage: storage });
    const videoSubscribers = new Set();

    app.post('/upload', upload.single('file'), (req, res) => {
        if (!req.file) {
            return res.status(400).send('No file uploaded.');
        }
        const base64Data = req.file.buffer.toString('base64');
        for (let socketId of videoSubscribers) {
            io.to(socketId).emit('video_frame', base64Data);
        }
        res.status(200).send('File uploaded successfully.');
    });

    io.on('connection', (socket) => {
        console.log('Video client connected:', socket.id);
        socket.on('subscribe_video', () => {
            videoSubscribers.add(socket.id);
            console.log('New subscriber:', socket.id);
        });

        socket.on('disconnect', () => {
            videoSubscribers.delete(socket.id);
            console.log('Subscriber disconnected:', socket.id);
        });
    });

    return { videoSubscribers };
}
module.exports = { startCameraService };