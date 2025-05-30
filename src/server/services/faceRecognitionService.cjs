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

const CONFIRMATION_WINDOW_SIZE = 5;
const MIN_CONSENSUS_THRESHOLD = 0.6;
const SESSION_TIMEOUT = 30000;

const faceDatabase = {
    nextId: 1,
    users: [],
}

const detectionSessions = new Map();

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
        console.error('Critical error saving database:', {
            message: error.message,
            stack: error.stack,
            dbDir: DB_DIR,
            dbFile: DB_FILE
        });
        throw error;
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

function getOrCreateDetectionSession(sessionId) {
    if (!detectionSessions.has(sessionId)) {
        detectionSessions.set(sessionId, {
            detections: [],
            lastUpdated: Date.now(),
            confirmed: false
        });
    }
    const session = detectionSessions.get(sessionId);
    session.lastUpdated = Date.now();

    return session;
}

function cleanupExpiredSessions() {
    const now = Date.now();
    for (const [sessionId, session] of detectionSessions.entries()) {
        if (now - session.lastUpdated > SESSION_TIMEOUT) {
            detectionSessions.delete(sessionId);
            console.log(`Session ${sessionId} expired and removed.`);
        }
    }
}

function analyzeDetectionConsensus(detections) {
    if (detections.length === 0) return null;

    const userCounts = {};
    let unkwnownUsersCount = 0;
    let totalDetections = 0;

    for (const detection of detections) {
        const userId = detection.result.userId;
        if (userId.startsWith('temp_user') || userId === 'unknown') {
            unkwnownUsersCount++;
        } else {
            userCounts[userId] = (userCounts[userId] || 0) + 1;
        }
        totalDetections++;
    }

    if (unkwnownUsersCount > 0) userCounts['UNKNOWN_USER'] = unkwnownUsersCount;

    let mostDetectedUser = null;
    let highestCount = 0;

    for (const [userId, count] of Object.entries(userCounts)) {
        if (count > highestCount) {
            highestCount = count;
            mostDetectedUser = userId;
        }
    }

    const consensusRatio = highestCount / totalDetections;
    const hasConsensus = consensusRatio >= MIN_CONSENSUS_THRESHOLD;

    if (hasConsensus) {
        if (mostDetectedUser === 'UNKNOWN_USER') {

            const unknownDetections = detections.filter(d => d.result.userId.startsWith('temp_user') || d.result.userId === 'unknown');
            if (unknownDetections.length === 0) {
                console.error('No detections found for the most detected user:');
                return null;
            }
            const newUserId = `temp_user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            return {
                confirmedUserId: newUserId,
                consensusRatio,
                bestDetection: {
                    userId: newUserId,
                    userName: 'unknown',
                    isNewUser: true,
                    needsIdentification: true,
                    distance: null
                },
                descriptorForAverage: unknownDetections.map(d => d.descriptor)
            };
        } else {

            const detectionsForUser = detections.filter(d => d.result.userId === mostDetectedUser);
            if (detectionsForUser.length === 0) {
                console.error('No detections found for the most detected user:');
                return null;
            }
            const bestDetection = detectionsForUser.reduce((best, current) => {
                if (!best) return current;
                const bestDistance = best.result.distance || Number.MAX_SAFE_INTEGER;
                const currentDistance = current.result.distance || Number.MAX_SAFE_INTEGER;
                return currentDistance < bestDistance ? current : best;
            }, null);

            return {
                confirmedUserId: mostDetectedUser,
                consensusRatio,
                bestDetection: bestDetection.result,
                descriptorForAverage: detections.filter(d => d.result.userId === mostDetectedUser).map(d => d.descriptor)
            };
        }
    }
    return null;
}

async function extractFaceDescriptor(imageBuffer) {
    try {
        console.log('Extracting face descriptor from image buffer...');
        if (!imageBuffer || imageBuffer.length === 0) {
            console.error('Invalid image buffer provided for face descriptor extraction.');
            return null;
        }

        console.log(`Processing image buffer of size: ${imageBuffer.length} bytes`);

        const img = await canvas.loadImage(imageBuffer);

        console.log(`Image loaded successfully: ${img.width}x${img.height}`);

        const detections = await faceapi.detectSingleFace(img).withFaceLandmarks().withFaceDescriptor();
        if (!detections) {
            console.error('No face detected in the image.');
            return null;
        }
        console.log('Face detected successfully.');

        const descriptor = Array.from(detections.descriptor);
        if (!isDescriptorValid(descriptor)) {
            console.error('Invalid face descriptor extracted from the image.');
            return null;
        }

        console.log(`Face descriptor extracted successfully: ${descriptor.length} dimensions`);
        return descriptor;
    } catch (error) {
        console.error('Error extracting face descriptor:', {
            message: error.message,
            stack: error.stack,
            bufferSize: imageBuffer?.length || 'undefined'
        });
        return null;
    }
}

async function recognizeFaceWithConfirmation(faceBuffer, sessionId, knownUserId = null) {
    try {
        console.log('=== FACE RECOGNITION SERVICE START ===');
        console.log(`SessionId: ${sessionId}, KnownUserId: ${knownUserId || 'none'}`);
        console.log(`Buffer size: ${faceBuffer?.length || 'undefined'} bytes`);

        if (!modelLoaded) await initFaceApi();
        if (!sessionId) return { error: 'Session ID is required.' };

        if (Math.random() < 0.1) {
            console.log('Performing periodic cleanup of expired sessions...');
            cleanupExpiredSessions();
        }

        console.log('Extracting face descriptor from the provided image buffer...');
        const newDescriptor = await extractFaceDescriptor(faceBuffer);
        if (!newDescriptor) return { error: 'No face detected in the image.' };

        console.log('Performing single face detection...');
        const detectionResult = await performSingleDetection(newDescriptor, knownUserId);
        console.log('Single detection result:', {
            userId: detectionResult.userId,
            userName: detectionResult.userName,
            isNewUser: detectionResult.isNewUser,
            error: detectionResult.error
        });

        console.log('Updating detection session with new descriptor...');
        const session = getOrCreateDetectionSession(sessionId);

        if (!session.detections) session.detections = [];

        session.detections.push({
            descriptor: newDescriptor,
            result: detectionResult,
            timestamp: Date.now()
        });

        console.log(`Session ${sessionId} updated with new detection. Total detections: ${session.detections.length}`);

        if (session.detections.length < CONFIRMATION_WINDOW_SIZE) {
            return {
                ...detectionResult,
                isPreliminary: true,
                detectionProgress: session.detections.length,
                totalRequired: CONFIRMATION_WINDOW_SIZE
            };
        }

        const consensus = analyzeDetectionConsensus(session.detections);

        if (consensus) {
            const confirmedResult = await confirmUserIdentity(
                consensus.confirmedUserId,
                consensus.descriptorForAverage,
                consensus.bestDetection
            );

            session.confirmed = true;

            console.log('=== FACE RECOGNITION SERVICE SUCCESS ===');
            return {
                ...confirmedResult,
                isConfirmed: true,
                consensusRatio: consensus.consensusRatio,
                detectionProgress: session.detections.length,
                totalRequired: CONFIRMATION_WINDOW_SIZE
            };
        } else {
            return {
                userId: 'uncertain',
                userName: 'unknown',
                isNewUser: false,
                needsIdentification: true,
                isUncertain: true,
                detectionProgress: session.detections.length,
                totalRequired: CONFIRMATION_WINDOW_SIZE,
                consensusRatio: 0
            };
        }
    } catch (error) {
        console.error('=== FACE RECOGNITION SERVICE ERROR ===');
        console.error('Unexpected error in recognizeFaceWithConfirmation:', {
            message: error.message,
            stack: error.stack,
            sessionId,
            knownUserId,
            bufferSize: faceBuffer?.length
        });
        console.error('============================================');
        return { error: 'Internal server error.' };
    }
}

async function performSingleDetection(newDescriptor, knownUserId) {
    try {
        if (knownUserId && knownUserId !== 'unknown') {
            console.log(`Checking known user ${knownUserId}...`);
            const userIndex = faceDatabase.users.findIndex(u => u.userId === knownUserId);

            if (userIndex >= 0) {
                const user = faceDatabase.users[userIndex];
                const distance = calculateEuclideanDistance(newDescriptor, user.descriptor);

                if (distance < EUCLIDEAN_DISTANCE_THRESHOLD) {
                    return {
                        userId: knownUserId,
                        userName: user.userName || 'unknown',
                        isNewUser: false,
                        distance: distance,
                        needsIdentification: !user.userName
                    };
                }
            }
        }

        console.log(`Searching among ${faceDatabase.users.length} existing users...`);
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
            console.log(`Best match found: ${bestMatch.userId} with distance ${lowestDistance}`);
            return {
                userId: bestMatch.userId,
                userName: bestMatch.userName || 'unknown',
                isNewUser: false,
                distance: lowestDistance,
                totalVisits: bestMatch.metadata.visits,
                needsIdentification: !bestMatch.userName
            };
        } else {
            const newUserId = `user${faceDatabase.nextId++}`;

            const newUser = {
                userId: newUserId,
                userName: null,
                descriptor: newDescriptor,
                descriptorHistory: [newDescriptor],
                metadata: {
                    createdAt: new Date().toISOString(),
                    lastSeen: new Date().toISOString(),
                    visits: 1,
                    isTemporary: false
                }
            };

            faceDatabase.users.push(newUser);
            console.log(`New user ${newUserId} detected and added to database`);

            try {
                await saveDatabaseToFile();
            } catch (error) {
                console.error('Failed to save database after creating new user:', saveError);
                faceDatabase.users.pop();
                faceDatabase.nextId--;
                throw saveError;
            }


            return {
                userId: newUserId,
                userName: 'unknown',
                isNewUser: true,
                needsIdentification: true,
                distance: null
            };
        }
    } catch (error) {
        console.error('Error performing single detection:', {
            message: error.message,
            stack: error.stack,
            knownUserId,
            descriptorLength: newDescriptor?.length
        });
        return { error: 'Internal server error in single detection.' };
    }
}

async function confirmUserIdentity(confirmedUserId, descriptors, bestDetectionResult) {
    try {
        if (!confirmedUserId) {
            console.error('confirmedUserId is required');
            return { error: 'User ID is required' };
        }

        if (!descriptors || !Array.isArray(descriptors) || descriptors.length === 0) {
            console.error('Valid descriptors array is required');
            return { error: 'Valid descriptors required' };
        }

        const userIndex = faceDatabase.users.findIndex(u => u.userId === confirmedUserId);

        if (userIndex >= 0) {
            const user = faceDatabase.users[userIndex];

            if (!user.descriptorHistory || !Array.isArray(user.descriptorHistory)) {
                user.descriptorHistory = user.descriptor ? [user.descriptor] : [];
            }

            const validDescriptors = descriptors.filter(desc =>
                desc && Array.isArray(desc) && desc.length === 128
            );

            if (validDescriptors.length > 0) {
                user.descriptorHistory.push(...validDescriptors);

                if (user.descriptorHistory.length > MAX_DESCRIPTOR_HISTORY) {
                    user.descriptorHistory = user.descriptorHistory.slice(-MAX_DESCRIPTOR_HISTORY);
                }

                user.descriptor = averageDescriptors(user.descriptorHistory);
            }

            if (!user.metadata) {
                user.metadata = {
                    createdAt: new Date().toISOString(),
                    visits: 1
                };
            }

            user.metadata.lastSeen = new Date().toISOString();
            user.metadata.visits = (user.metadata.visits || 0) + 1;

            await saveDatabaseToFile();

            return {
                userId: confirmedUserId,
                userName: user.userName || 'unknown',
                isNewUser: user.metadata.visits === 1,
                distance: bestDetectionResult?.distance || null,
                totalVisits: user.metadata.visits,
                needsIdentification: !user.userName
            };
        } else {
            console.error(`User ${confirmedUserId} not found in database`);
            return { error: 'User not found in the database.' };
        }
    } catch (error) {
        console.error('Error confirming user identity:', error);
        return { error: 'Internal server error confirming user identity.' };
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
    console.log('Active detection sessions:', detectionSessions.size);
    faceDatabase.users.forEach(user => {
        console.log(`- ${user.userId} (${user.userName || 'unnamed'}): ${user.metadata.visits} visits, descriptor length: ${user.descriptor ? user.descriptor.length : 'null'}`);
    })

    for (const [sessionId, session] of detectionSessions.entries()) {
        console.log(`Session ${sessionId}: ${session.detections.length} detections, confirmed: ${session.confirmed}, last updated: ${new Date(session.lastUpdated).toISOString()}`);
    }
}

function listAllUsers() {
    return faceDatabase.users.map(user => ({
        userId: user.userId,
        userName: user.userName,
        ...user.metadata,
        descriptorSamples: user.descriptorHistory.length ? user.descriptorHistory.length : 1
    }));
}

function getDetectionSessionStats() {
    return {
        activeSessions: detectionSessions.size,
        sessions: Array.from(detectionSessions.entries()).map(([sessionId, session]) => ({
            sessionId,
            detectionsCount: session.detections.length,
            confirmed: session.confirmed,
            lastUpdated: session.lastUpdated,
            age: Date.now() - session.lastUpdated
        }))
    }
}

(async () => {
    await initFaceApi();
    await loadDatabaseFromFile();
})();

module.exports = {
    recognizeFaceWithConfirmation,
    listAllUsers,
    findUserByName,
    updateUserName,
    debugDatabase,
    getDetectionSessionStats
};