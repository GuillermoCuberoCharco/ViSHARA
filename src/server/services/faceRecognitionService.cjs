const fs = require('fs').promises;
const path = require('path');
const faceapi = require('@vladmandic/face-api');
const canvas = require('canvas');
const { Canvas, Image, ImageData } = canvas;
faceapi.env.monkeyPatch({ Canvas, Image, ImageData });

const MODELS_PATH = path.join(__dirname, '..', 'models');
const DB_DIR = path.join(__dirname, '..', 'data');
const DB_FILE = path.join(DB_DIR, 'faceDatabase.json');

const faceDatabase = {
    nextId: 1,
    users: [],
}

let modelLoaded = false;

async function initFaceApi() {
    try {
        if (modelLoaded) return;

        await fs.mkdir(MODELS_PATH, { recursive: true });

        await faceapi.nets.ssdMobilenetv1.loadFromDisk(MODELS_PATH);
        await faceapi.nets.faceLandmark68Net.loadFromDisk(MODELS_PATH);
        await faceapi.nets.faceRecognitionNet.loadFromDisk(MODELS_PATH);

        modelLoaded = true;
        console.log('Face API models loaded successfully.');
    } catch (error) {
        console.error('Error loading Face API models:', error);
    }
}

async function loadDatabaseFromFile() {
    try {
        await fs.mkdir(DB_DIR, { recursive: true });

        const data = await fs.readFile(DB_FILE, 'utf-8');
        const loadedData = JSON.parse(data);

        faceDatabase.nextId = loadedData.nextId || 1;
        faceDatabase.users = loadedData.users || [];
        console.log(`Database loaded successfully: ${faceDatabase.users.length} users.`);
    } catch (error) {
        if (error.code !== 'ENOENT') {
            console.error('Error loading database:', error);
        } else {
            console.log('Database file not found. Starting with an empty database.');
            await saveDatabaseToFile();
        }
    }
}

async function saveDatabaseToFile() {
    try {
        await fs.mkdir(DB_DIR, { recursive: true });
        await fs.writeFile(
            DB_FILE,
            JSON.stringify(faceDatabase, null, 2),
            'utf-8'
        );
        console.log('Database saved successfully.');
    } catch (error) {
        console.error('Error saving database:', error);
    }
}

function calculateSimilarity(descriptor1, descriptor2) {
    if (!descriptor1 || !descriptor2 || !Array.isArray(descriptor1) || !Array.isArray(descriptor2)) {
        return 0;
    }

    let sum = 0;
    for (let i = 0; i < descriptor1.length; i++) {
        const diff = descriptor1[i] - descriptor2[i];
        sum += diff * diff;
    }
    const distance = Math.sqrt(sum);

    // Convertir distancia a similitud (0-1)
    // 0.5 es un umbral un poco estricto para face-api.js (lo más común es 0.6)
    const similarity = Math.max(0, 1 - distance / 0.5);
    return similarity;
}

function averageDescriptors(descriptors) {
    if (!descriptors || descriptors.length === 0) return null;
    if (descriptors.length === 1) return descriptors[0];

    const averaged = new Array(descriptors[0].length).fill(0);

    for (const descriptor of descriptors) {
        for (let i = 0; i < descriptor.length; i++) {
            averaged[i] += descriptor[i];
        }
    }
    for (let i = 0; i < averaged.length; i++) {
        averaged[i] /= descriptors.length;
    }
    return averaged;
}

function isDescriptorValid(descriptor, existingDescriptors = []) {
    if (!descriptor || !Array.isArray(descriptor)) return false;

    const magnitude = Math.sqrt(descriptor.reduce((sum, val) => sum + val * val, 0));
    if (magnitude < 0.1 || magnitude > 10) return false;

    if (existingDescriptors.length > 0) {
        const avgSimilarity = existingDescriptors.reduce((sum, existing) => sum + calculateSimilarity(descriptor, existing), 0) / existingDescriptors.length;

        return avgSimilarity > 0.4 && avgSimilarity < 0.95;
    }

    return true;
}

async function extractFaceDescriptor(imageBuffer) {
    try {
        const img = await canvas.loadImage(imageBuffer);

        const detections = await faceapi.detectSingleFace(img).withFaceLandmarks().withFaceDescriptor();

        if (!detections) return null;

        return Array.from(detections.descriptor);
    } catch (error) {
        console.error('Error extracting face descriptor:', error);
        return null;
    }
}

async function recogniceFace(faceBuffer, knownUserId = null) {
    try {
        if (!modelLoaded) await initFaceApi();

        const newDescriptor = await extractFaceDescriptor(faceBuffer);
        if (!newDescriptor) return { error: 'No face detected in the image.' };

        if (knownUserId) {
            const userIndex = faceDatabase.users.findIndex(u => u.userId === knownUserId);

            if (userIndex >= 0) {
                const user = faceDatabase.users[userIndex];

                if (isDescriptorValid(newDescriptor, user.descriptorHistory || [user.descriptor])) {
                    if (!user.descriptorHistory) user.descriptorHistory = [user.descriptor];

                    user.descriptorHistory.push(newDescriptor);

                    if (user.descriptorHistory.length > 5) {
                        user.descriptorHistory = user.descriptorHistory.slice(-5);
                    }

                    user.descriptor = averageDescriptors(user.descriptorHistory);

                    console.log(`User ${knownUserId} updated in the database with ${user.descriptorHistory.length} samples.`);
                }

                user.metadata.lastSeen = new Date().toISOString();
                user.metadata.visits += 1;
                await saveDatabaseToFile();
                return { userId: knownUserId, isNewUser: false };
            }
        }

        let bestMatch = null;
        let highetSimilarity = 0;

        for (const user of faceDatabase.users) {
            if (!user.descriptor) continue;

            const similarity = calculateSimilarity(newDescriptor, user.descriptor);
            console.log(`Similarity with ${user.userId}: ${similarity.toFixed(3)}`);
            if (similarity > 0.7 && similarity > highetSimilarity) {
                highetSimilarity = similarity;
                bestMatch = user;
            }
        }

        if (bestMatch) {
            if (isDescriptorValid(newDescriptor, bestMatch.descriptorHistory || [bestMatch.descriptor])) {

                if (!bestMatch.descriptorHistory) bestMatch.descriptorHistory = [bestMatch.descriptor];

                bestMatch.descriptorHistory.push(newDescriptor);

                if (bestMatch.descriptorHistory.length > 5) {
                    bestMatch.descriptorHistory = bestMatch.descriptorHistory.slice(-5);
                }

                bestMatch.descriptor = averageDescriptors(bestMatch.descriptorHistory);
                console.log(`User ${bestMatch.userId} descriptor improved in the database with ${bestMatch.descriptorHistory.length} samples.`);
            }

            bestMatch.metadata.lastSeen = new Date().toISOString();
            bestMatch.metadata.visits += 1;
            await saveDatabaseToFile();
            return { userId: bestMatch.userId, isNewUser: false, similarity: highetSimilarity };
        } else {
            if (!isDescriptorValid(newDescriptor)) return { error: 'Invalid face descriptor.' };

            const newUserId = `user${faceDatabase.nextId++}`;
            faceDatabase.users.push({
                userId: newUserId,
                descriptor: newDescriptor,
                metadata: {
                    createdAt: new Date().toISOString(),
                    lastSeen: new Date().toISOString(),
                    visits: 1
                },
            });

            console.log(`New user ${newUserId} added to the database.`);
            await saveDatabaseToFile();
            return { userId: newUserId, isNewUser: true };
        }
    } catch (error) {
        console.error('Error recognizing face:', error);
        return { error: 'Internal server error.' };
    }
}

function listAllUsers() {
    return faceDatabase.users.map(user => ({
        userId: user.userId,
        ...user.metadata
    }));
}

(async () => {
    await initFaceApi();
    await loadDatabaseFromFile();
})();

module.exports = {
    recogniceFace,
    listAllUsers
};