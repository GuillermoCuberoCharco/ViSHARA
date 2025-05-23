const fs = require('fs').promises;
const path = require('path');
const faceapi = require('@vladmandic/face-api');
const canvas = require('canvas');
const { Canvas, Image, ImageData } = canvas;
faceapi.env.monkeyPatch({ Canvas, Image, ImageData });

const MODELS_PATH = path.join(__dirname, '..', 'models');
const DB_DIR = path.join(__dirname, '..', 'data');
const DB_FILE = path.join(DB_DIR, 'faceDatabase.json');

// CONFIGURATION FOR FACE-API.JS (Based on face-api.js documentation)
const EUCLIDEAN_DISTANCE_THRESHOLD = 0.6;
const MIN_DESCRIPTOR_QUALITY = 0.1;
const MAX_DESCRIPTOR_HISTORY = 3;

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

function calculateEuclideanDistance(descriptor1, descriptor2) {
    if (!descriptor1 || !descriptor2 || !Array.isArray(descriptor1) || !Array.isArray(descriptor2)) return Number.MAX_SAFE_INTEGER;

    if (descriptor1.length !== descriptor2.length) return Number.MAX_SAFE_INTEGER;

    let sum = 0;
    for (let i = 0; i < descriptor1.length; i++) {
        const diff = descriptor1[i] - descriptor2[i];
        sum += diff * diff;
    }
    const distance = Math.sqrt(sum);

    return distance;
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

    if (descriptor.length !== 128) return false;

    const magnitude = Math.sqrt(descriptor.reduce((sum, val) => sum + val * val, 0));
    if (magnitude < MIN_DESCRIPTOR_QUALITY) return false;

    return true;
}

async function extractFaceDescriptor(imageBuffer) {
    try {
        const img = await canvas.loadImage(imageBuffer);

        const detections = await faceapi.detectSingleFace(img).withFaceLandmarks().withFaceDescriptor();
        if (!detections) return null;

        const descriptor = Array.from(detections.descriptor);
        if (!isDescriptorValid(descriptor)) return null;

        return descriptor;
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

        console.log('Database has', faceDatabase.users.length, 'users')

        if (knownUserId && knownUserId !== 'unknwon') {
            const userIndex = faceDatabase.users.findIndex(u => u.userId === knownUserId);

            if (userIndex >= 0) {
                const user = faceDatabase.users[userIndex];
                const distance = calculateEuclideanDistance(newDescriptor, user.descriptor);

                if (distance < EUCLIDEAN_DISTANCE_THRESHOLD) {
                    if (!user.descriptorHistory) user.descriptorHistory = [user.descriptor];

                    user.descriptorHistory.push(newDescriptor);

                    if (user.descriptorHistory.length > MAX_DESCRIPTOR_HISTORY) {
                        user.descriptorHistory = user.descriptorHistory.slice(-MAX_DESCRIPTOR_HISTORY);
                    }

                    user.descriptor = averageDescriptors(user.descriptorHistory);
                    user.metadata.lastSeen = new Date().toISOString();
                    user.metadata.visits += 1;
                    await saveDatabaseToFile();
                    return {
                        userId: knownUserId,
                        userName: user.userName || knownUserId,
                        isNewUser: false,
                        distance: distance,
                        needsIdentification: !user.userName
                    };
                }
            }
        }

        let bestMatch = null;
        let lowestDistance = Number.MAX_SAFE_INTEGER;

        for (const user of faceDatabase.users) {
            if (!user.descriptor || !isDescriptorValid(user.descriptor)) continue;

            const distance = calculateEuclideanDistance(newDescriptor, user.descriptor);

            if (distance < EUCLIDEAN_DISTANCE_THRESHOLD && distance < lowestDistance) {
                bestMatch = user;
                lowestDistance = distance;
            }
        }

        if (bestMatch) {
            if (!bestMatch.descriptorHistory) bestMatch.descriptorHistory = [bestMatch.descriptor];

            bestMatch.descriptorHistory.push(newDescriptor);

            if (bestMatch.descriptorHistory.length > MAX_DESCRIPTOR_HISTORY) {
                bestMatch.descriptorHistory = bestMatch.descriptorHistory.slice(-MAX_DESCRIPTOR_HISTORY);
            }

            bestMatch.descriptor = averageDescriptors(bestMatch.descriptorHistory);
            bestMatch.metadata.lastSeen = new Date().toISOString();
            bestMatch.metadata.visits += 1;

            await saveDatabaseToFile();

            return {
                userId: bestMatch.userId,
                userName: bestMatch.userName || bestMatch.userId,
                isNewUser: false,
                distance: lowestDistance,
                totalVisits: bestMatch.metadata.visits,
                needsIdentification: !bestMatch.userName
            };
        } else {

            const tempUserId = `temp${faceDatabase.nextId++}`;

            faceDatabase.users.push({
                userId: tempUserId,
                userName: null,
                descriptor: newDescriptor,
                descriptorHistory: [newDescriptor],
                metadata: {
                    createdAt: new Date().toISOString(),
                    lastSeen: new Date().toISOString(),
                    visits: 1,
                    isTemporary: true
                },
            });

            console.log(`New unknwon user ${tempUserId} added to the database.`);
            await saveDatabaseToFile();
            return {
                userId: tempUserId,
                userName: 'unknwon',
                isNewUser: true,
                needsIdentification: true,
                totalUsers: faceDatabase.users.length
            };
        }
    } catch (error) {
        console.error('Error recognizing face:', error);
        return { error: 'Internal server error.' };
    }
}

async function updateUserName(userId, userName) {
    try {
        const userIndex = faceDatabase.users.findIndex(u => u.userId === userId);

        if (userIndex >= 0) {
            const user = faceDatabase.users[userIndex];

            if (user.metadata.isTemporary) {
                const newUserId = `user${faceDatabase.nextId++}`;
                user.userId = newUserId;
                user.metadata.isTemporary = false;
            }

            user.userName = userName;
            user.metadata.idetifiedAt = new Date().toISOString();
            await saveDatabaseToFile();
            return {
                success: true,
                userId: user.userId,
                userName: user.userName,
                oldUserId: user.userId
            };
        }

        return {
            success: false,
            error: 'User not found.'
        };
    } catch (error) {
        console.error('Error updating user name:', error);
        return {
            success: false,
            error: 'Internal server error.'
        };
    }
}

function findUserByName(userName) {
    return faceDatabase.users.find(u => u.userName && u.userName.toLowerCase() === userName.toLowerCase());
}

function debugDatabase() {
    console.log('DATABASE DEBUG:');
    console.log('Total users:', faceDatabase.users.length);
    faceDatabase.users.forEach(user => {
        console.log(`- ${user.userId} (${user.userName || 'unnamed'}): ${user.metadata.visits} visits, descriptor length: ${user.descriptor ? user.descriptor.length : 'null'}`);
    })
}

function listAllUsers() {
    return faceDatabase.users.map(user => ({
        userId: user.userId,
        userName: user.userName,
        ...user.metadata,
        descriptorSamples: user.descriptorHistory.length ? user.descriptorHistory.length : 1
    }));
}

(async () => {
    await initFaceApi();
    await loadDatabaseFromFile();
})();

module.exports = {
    recogniceFace,
    listAllUsers,
    findUserByName,
    updateUserName,
    debugDatabase
};