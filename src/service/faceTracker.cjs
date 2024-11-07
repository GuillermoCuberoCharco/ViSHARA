const fs = require('fs');
const path = require('path');
const multer = require('multer');

class FaceTrackerService {
    constructor() {
        this.storage = multer.diskStorage({
            destination: (req, file, cb) => {
                const uploadDir = path.join(__dirname, 'uploads');
                if (!fs.existsSync(uploadDir)) {
                    fs.mkdirSync(uploadDir, { recursive: true });
                }
                cb(null, uploadDir);
            },
            filename: (req, file, cb) => {
                cb(null, `face_${Date.now()}_${file.originalname}`);
            }
        });

        this.upload = multer({
            storage: this.storage,
            limits: {
                fileSize: 5 * 1024 * 1024
            },
            fileFilter: (req, file, cb) => {
                if (!file.originalname.match(/\.(jpg|jpeg|png)$/)) {
                    return cb(new Error('Only image files are allowed!'), false);
                }
                cb(null, true);
            }
        });
    }

    setupRoutes(app) {
        app.post('/upload', this.upload.single('file'), (req, res) => {
            try {
                if (!req.file) {
                    return res.status(400).send('No file recived');
                }

                res.status(200).send({
                    message: 'Image uploaded successfully',
                    filename: req.file.filename
                });

            } catch (error) {
                console.error('Error processing upload:', error);
                res.status(500).send('Error procesing the image');
            }
        });
    }

    cleanupOldImages(maxAge = 24 * 60 * 60 * 1000) {
        const uploadDir = path.join(__dirname, 'uploads');

        try {
            if (!fs.existsSync(uploadDir)) return;

            const files = fs.readdirSync(uploadDir);
            const now = Date.now();

            files.forEach(file => {
                const filePath = path.join(uploadDir, file);
                const stats = fs.statSync(filePath);

                if (now - stats.mtime.getTime() > maxAge) {
                    fs.unlinkSync(filePath);
                    console.log(`Deleted old file: ${file}`);
                }
            });
        } catch (error) {
            console.error('Error cleaning up old images:', error);
        }
    }

}

module.exports = new FaceTrackerService();