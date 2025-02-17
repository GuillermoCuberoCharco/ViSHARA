const multer = require('multer');
const { recognizeFace, registerNewFace } = require('./faceRecognition');

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

    app.post('/recognize', upload.single('frame'), async (req, res) => {
        if (!req.file) {
            return res.status(400).send('No frame received');
        }

        try {
            const result = await recognizeFace(req.file.buffer);
            res.json(result);
        } catch (error) {
            console.error('Error recognizing face:', error);
            res.status(500).json({
                success: false,
                message: 'Error recognizing face'
            });
        }
    });

    app.post('/register-face', async (req, res) => {
        try {
            const { descriptor, userId, label } = req.body;
            if (!descriptor || !userId || !label) {
                return res.status(400).json({
                    success: false,
                    message: 'Missing required fields'
                });
            }
            const result = await registerNewFace(descriptor, userId, label);
            res.json(result);
        } catch {
            console.error('Error registering face:', error);
            res.status(500).json({
                success: false,
                message: 'Error registering face'
            });
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