const multer = require('multer');

function startCameraService(app, io) {
    const storage = multer.memoryStorage();
    const upload = multer({
        storage: storage,
        limits: { fileSize: 5 * 1024 * 1024 }
    });
    const videoSubscribers = new Set();

    app.get('/camera-status', (req, res) => {
        res.status(200).json({
            status: 'Camera service is running.',
            subscribers: videoSubscribers.size
        });
    });

    app.post('/upload', upload.single('file'), (req, res) => {
        if (!req.file) {
            console.log('No file received in upload request.');
            return res.status(400).send('No file uploaded.');
        }

        try {
            const base64Data = req.file.buffer.toString('base64');
            let subscribersReceived = 0;
            if (videoSubscribers.size > 0) {
                for (let socketId of videoSubscribers) {
                    io.to(socketId).emit('video_chunk', base64Data);
                    subscribersReceived++;
                }
                console.log(`Sent video chunk to ${subscribersReceived} subscribers.`);
            }
            res.status(200).send('File uploaded successfully.');
        } catch (error) {
            console.error('Error processing uploaded file:', error);
            res.status(500).send('Error processing file.');
        }
    });

    io.on('connection', (socket) => {
        console.log('Video client connected:', socket.id);
        socket.on('subscribe_video', () => {
            videoSubscribers.add(socket.id);
            console.log(`Client ${socket.id} subscribed to video. Total subscribers: ${videoSubscribers.size}`);
            socket.emit('subscription_confirmed', { status: 'ok' });
        });

        socket.on('unsubscribe_video', () => {
            videoSubscribers.delete(socket.id);
            console.log(`Client ${socket.id} unsubscribed from video. Total subscribers: ${videoSubscribers.size}`);
        });

        socket.on('disconnect', () => {
            if (videoSubscribers.has(socket.id)) {
                videoSubscribers.delete(socket.id);
                console.log(`Video subscriber disconnected: ${socket.id}`);
            }
        });
    });

    return { videoSubscribers };
}
module.exports = { startCameraService };