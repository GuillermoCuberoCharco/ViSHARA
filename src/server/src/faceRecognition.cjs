const faceapi = require('face-api.js');
const path = require('path');
const canvas = require('canvas');
const { timeStamp } = require('console');
const fs = require('fs').promises;
const { Canvas, Image, ImageData } = canvas;

// Simulamos el entorno de navegador para face-api
faceapi.env.monkeyPatch({ Canvas, Image, ImageData });

const MODEL_PATH = path.join(__dirname, '../models');
const KNOWN_FACES = path.join(__dirname, '../known_faces');
const DISTANCE_THRESHOLD = 0.6;

const knownFaces = new Map();

async function ensureDirectoryExists(directory) {
    try {
        await fs.access(directory);
    } catch {
        await fs.mkdir(directory, { recursive: true });
    }
}

async function loadModels() {
    try {
        await faceapi.nets.tinyFaceDetector.loadFromDisk(MODEL_PATH);
        await faceapi.nets.faceLandmark68Net.loadFromDisk(MODEL_PATH);
        await faceapi.nets.faceRecognitionNet.loadFromDisk(MODEL_PATH);
        console.log('Face-api models loaded (server)');
        await loadKnownFaces();
    } catch (error) {
        console.error('Error loading face-api models:', error);
        throw error;
    }
}

async function loadKnownFaces() {
    try {
        await ensureDirectoryExists(KNOWN_FACES);
        const files = await fs.readdir(KNOWN_FACES);

        for (const file of files) {
            if (file.endsWith('.json')) {
                const userId = file.replace('.json', '');
                const data = JSON.parse(
                    await fs.readFile(path.join(KNOWN_FACES, file), 'utf8')
                );
                knownFaces.set(userId, {
                    descriptor: new Float32Array(data.descriptor),
                    label: data.label
                });
            }
        }
        console.log(`Loaded ${knownFaces.size} known faces`);
    } catch (error) {
        console.log('Error loading known faces:', error);
    }
}

async function saveNewFace(descriptor, userId, label) {
    try {
        await ensureDirectoryExists(KNOWN_FACES);
        const faceData = {
            descriptor: Array.from(descriptor),
            label,
            timestamp: new Date().toISOString()
        };

        await fs.writeFile(
            path.join(KNOWN_FACES, `${userId}.json`),
            JSON.stringify(faceData, null, 2)
        );

        knownFaces.set(userId, {
            descriptor: new Float32Array(descriptor),
            label
        });

        return true;
    } catch (error) {
        console.error('Error saving new face:', error);
        return false;
    }
}

function findBestMatch(descriptor) {
    let bestMatch = null;
    let lowestDistance = Infinity;

    for (const [userId, knownFace] of knownFaces.entries()) {
        const distance = faceapi.euclideanDistance(descriptor, knownFace.descriptor);
        if (distance < lowestDistance) {
            lowestDistance = distance;
            bestMatch = {
                userId,
                label: knownFace.label,
                distance
            };
        }
    }

    if (bestMatch && lowestDistance <= DISTANCE_THRESHOLD) {
        return bestMatch;
    }

    return null;
}

async function recognizeFace(frameBuffer) {
    try {
        const img = await canvas.loadImage(frameBuffer);
        const detections = await faceapi
            .detectAllFaces(img, new faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceDescriptors();
        if (!detections.length) {
            return {
                success: false,
                message: 'No faces detected'
            };
        }

        const faceDescriptor = detections[0].descriptor;
        const match = findBestMatch(faceDescriptor);

        if (match) {
            return {
                success: true,
                isKnownFace: true,
                userId: match.userId,
                label: match.label,
                confidence: 1 - match.distance
            };
        } else {
            const newUserId = `user_${Date.now()}`;
            return {
                success: true,
                isKnownFace: false,
                descriptor: Array.from(faceDescriptor),
                suggestdUserId: newUserId
            };
        }
    } catch (error) {
        console.error('Error recognizing face:', error);
        return {
            success: false,
            message: error.message
        };
    }
}

async function registerNewFace(descriptor, userId, label) {
    if (Array.isArray(descriptor)) {
        descriptor = new Float32Array(descriptor);
    }

    const saved = await saveNewFace(descriptor, userId, label);
    return {
        success: saved,
        userId,
        message: saved ? 'Face registered successfully' : 'Error registering face'
    };
}

loadModels().catch(console.error);

module.exports = {
    recognizeFace,
    registerNewFace,
    loadKnownFaces
};