const multer = require('multer');
const { recognizeFace } = require('./faceRecognition.cjs');

function startCameraService(app, io) {
    const storage = multer.memoryStorage();
    const upload = multer({ storage: storage });
    const videoSubscribers = new Set();

    // Endpoint para recibir los frames y ejecutar el reconocimiento en el servidor
    app.post('/recognize', upload.single('frame'), async (req, res) => {
        if (req.file) {
            try {
                const detections = await recognizeFace(req.file.buffer);
                console.log('Detections (server):', detections);
                res.status(200).json({ detections });
            } catch (error) {
                console.error('Recognition error (server):', error);
                res.status(500).send('Recognition error');
            }
        } else {
            res.status(400).send('No frame received');
        }
    });

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

    app.post('/save-descriptors', (req, res) => {
        const { descriptors } = req.body;
        // Guardar los descriptores en una base de datos o archivo
        console.log('Saving descriptors:', descriptors);
        // Aquí puedes agregar la lógica para guardar los descriptores en una base de datos
        res.status(200).send('Descriptors saved');
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