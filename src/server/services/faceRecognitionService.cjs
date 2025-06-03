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
const EUCLIDEAN_DISTANCE_THRESHOLD = 0.45;
const MIN_DESCRIPTOR_QUALITY = 0.1;
const MAX_DESCRIPTOR_HISTORY = 3;

const CONFIRMATION_WINDOW_SIZE = 5;
const MIN_CONSENSUS_THRESHOLD = 0.8;
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

function isDescriptorValid(descriptor) {
    if (!descriptor || !Array.isArray(descriptor)) return false;

    if (descriptor.length !== 128) return false;

    const magnitude = Math.sqrt(descriptor.reduce((sum, val) => sum + val * val, 0));
    if (magnitude < MIN_DESCRIPTOR_QUALITY) return false;

    return true;
}

function getOrCreateDetectionSession(sessionId) {
    if (!detectionSessions.has(sessionId)) {
        detectionSessions.set(sessionId, {
            descriptors: [],
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

function findBestMatchForDescriptor(descriptor, knownUserId = null) {

    if (knownUserId && knownUserId !== 'unknown') {
        const user = faceDatabase.users.find(u => u.userId === knownUserId);
        if (user) {
            const distance = calculateEuclideanDistance(descriptor, user.descriptor);
            if (distance < EUCLIDEAN_DISTANCE_THRESHOLD) {
                return {
                    userId: knownUserId,
                    userName: user.userName || 'unknown',
                    distance: distance,
                    confidence: 1 - Math.min(distance, 1),
                    needsIdentification: !user.userName
                };
            }
        }
    }

    let bestMatch = null;
    let lowestDistance = Number.MAX_SAFE_INTEGER;

    for (const user of faceDatabase.users) {
        if (!user.descriptor || !isDescriptorValid(user.descriptor)) continue;

        const distance = calculateEuclideanDistance(descriptor, user.descriptor);
        if (distance < EUCLIDEAN_DISTANCE_THRESHOLD && distance < lowestDistance) {
            bestMatch = user;
            lowestDistance = distance;
        }
    }

    if (bestMatch) {
        return {
            userId: bestMatch.userId,
            userName: bestMatch.userName || 'unknown',
            distance: lowestDistance,
            needsIdentification: !bestMatch.userName,
            totalVisits: bestMatch.metadata.visits
        };
    }

    return {
        userId: 'unknown',
        userName: 'unknown',
        distance: null,
        confidence: 0,
        needsIdentification: true
    };
}

function analyzeDescriptorBatch(descriptors, knownUserId = null) {
    console.log(`\n=== ANALYZING BATCH OF ${descriptors.length} DESCRIPTORS ===`);

    const detectionResults = [];

    descriptors.forEach((descriptor, index) => {
        const result = findBestMatchForDescriptor(descriptor, knownUserId);
        detectionResults.push(result);
        console.log(`Descriptor ${index + 1}: ${result.userId} (distance: ${result.distance ? result.distance.toFixed(3) : 'N/A'})`);
    });

    const userVotes = {};
    detectionResults.forEach(result => {
        const userId = result.userId;
        if (!userVotes[userId]) {
            userVotes[userId] = { count: 0, results: [], avgDistance: 0 };
        }
        userVotes[userId].count++;
        userVotes[userId].results.push(result);
    });

    Object.keys(userVotes).forEach(userId => {
        const validDistances = userVotes[userId].results
            .map(r => r.distance)
            .filter(d => d !== null);

        userVotes[userId].avgDistance = validDistances.length > 0
            ? validDistances.reduce((sum, d) => sum + d, 0) / validDistances.length
            : 0;
    });

    console.log('=== VOTE SUMMARY ===');
    Object.entries(userVotes).forEach(([userId, vote]) => {
        console.log(`User ${userId}: ${vote.count} votes, Avg Distance: ${vote.avgDistance.toFixed(3)}`);
    });

    let winnerUserId = null;
    let maxVotes = 0;

    Object.entries(userVotes).forEach(([userId, vote]) => {
        if (vote.count > maxVotes) {
            maxVotes = vote.count;
            winnerUserId = userId;
        }
    });

    const consensusRatio = maxVotes / descriptors.length;
    const hasConsensus = consensusRatio >= MIN_CONSENSUS_THRESHOLD;
    console.log(`\n=== CONSENSUS ANALYSIS ===`);
    console.log(`Winner: ${winnerUserId} with ${maxVotes}/${descriptors.length} votes (${(consensusRatio * 100).toFixed(1)}%)`);
    console.log(`Consensus reached: ${hasConsensus} (required: ${(MIN_CONSENSUS_THRESHOLD * 100).toFixed(1)}%)`);

    if (!hasConsensus) {
        return {
            isUncertain: true,
            consensusRatio: consensusRatio,
            userId: 'uncertain',
            userName: 'unknown',
            needsIdentification: true
        };
    }

    const winnerDescriptors = userVotes[winnerUserId].results.map((result, index) => {
        const originalIndex = descriptors.findIndex(r => r === result);
        return descriptors[originalIndex];
    });

    const winnerResult = userVotes[winnerUserId].results[0];

    return {
        isConfirmed: true,
        consensusRatio: consensusRatio,
        userId: winnerUserId,
        userName: winnerResult.userName,
        needsIdentification: winnerResult.needsIdentification,
        distance: userVotes[winnerUserId].avgDistance,
        confidence: winnerResult.confidence,
        isNewUser: winnerUserId === 'unknown',
        descriptorsForUpdate: winnerDescriptors,
        totalVisits: winnerResult.totalVisits
    };
}

async function extractFaceDescriptor(imageBuffer) {
    try {
        if (!imageBuffer || imageBuffer.length === 0) {
            console.error('Invalid image buffer provided for face descriptor extraction.');
            return null;
        }

        const img = await canvas.loadImage(imageBuffer);
        const detections = await faceapi.detectSingleFace(img).withFaceLandmarks().withFaceDescriptor();

        if (!detections) {
            console.error('No face detected in the image.');
            return null;
        }

        const descriptor = Array.from(detections.descriptor);
        if (!isDescriptorValid(descriptor)) {
            console.error('Invalid face descriptor extracted from the image.');
            return null;
        }

        return descriptor;
    } catch (error) {
        console.error('Error extracting face descriptor:', error);
        return null;
    }
}

async function recognizeFaceWithBatch(faceBuffers, sessionId, knownUserId = null) {
    try {
        console.log('=== BATCH FACE RECOGNITION SERVICE START ===');
        console.log(`SessionId: ${sessionId}, KnownUserId: ${knownUserId || 'none'}`);

        if (!modelLoaded) await initFaceApi();
        if (!sessionId) return { error: 'Session ID is required.' };
        if (!faceBuffers || faceBuffers.length === 0) return { error: 'No face buffers provided.' };

        const descriptors = [];
        for (let i = 0; i < faceBuffers.length; i++) {
            console.log(`Processing face buffer ${i + 1}/${faceBuffers.length}...`);
            const descriptor = await extractFaceDescriptor(faceBuffers[i]);
            if (descriptor) {
                descriptors.push(descriptor);
            } else {
                console.warn(`No face detected in buffer ${i + 1}.`);
            }
        }

        if (descriptors.length === 0) return { error: 'No valid face descriptors extracted from the provided images.' };

        console.log(`Successfully extracted ${descriptors.length} descriptors from ${faceBuffers.length} images`);

        const result = analyzeDescriptorBatch(descriptors, knownUserId);

        if (result.isUncertain) {
            console.log('=== UNCERTAIN RESULT ===');
            return {
                ...result,
                detectionProgress: descriptors.length,
                totalRequired: CONFIRMATION_WINDOW_SIZE,
            };
        }

        if (result.isConfirmed) {
            const confirmedResult = await confirmUserIdentityWithDescriptor(
                result.userId,
                result.descriptorsForUpdate,
                result
            );

            console.log('=== BATCH FACE RECOGNITION SUCCESS ===');
            return {
                ...confirmedResult,
                isConfirmed: true,
                consensusRatio: result.consensusRatio,
                detectionProgress: descriptors.length,
                totalRequired: CONFIRMATION_WINDOW_SIZE
            };
        }

        return result;

    } catch (error) {
        console.error('=== BATCH FACE RECOGNITION SERVICE ERROR ===');
        console.error('Unexpected error in recognizeFaceWithBatch:', {
            message: error.message,
            stack: error.stack,
            sessionId,
            knownUserId,
            bufferCount: faceBuffers?.length
        });
        console.error('============================================');
        return { error: 'Internal server error.' };
    }
}

async function confirmUserIdentityWithDescriptor(userId, descriptorsToUpdate, resultData) {
    try {
        console.log(`\n=== CONFIRMING USER IDENTITY ===`);
        console.log(`UserId: ${userId}, Descriptors: ${descriptorsToUpdate.length}`);

        if (userId === 'unknown') {
            const newUserId = `user${faceDatabase.nextId++}`;
            const newUser = {
                userId: newUserId,
                userName: null,
                descriptor: averageDescriptors(descriptorsToUpdate),
                descriptorHistory: [...descriptorsToUpdate],
                metadata: {
                    createdAt: new Date().toISOString(),
                    lastSeen: new Date().toISOString(),
                    visits: 1,
                    isTemporary: true
                }
            };

            faceDatabase.users.push(newUser);
            console.log(`NEW USER CREATED: ${newUserId} with ${descriptorsToUpdate.length} descriptors`);

            await saveDatabaseToFile();

            return {
                userId: newUserId,
                userName: 'unknown',
                isNewUser: true,
                needsIdentification: true,
                distance: resultData.distance,
                confidence: resultData.confidence
            };
        } else {
            const userIndex = faceDatabase.users.findIndex(u => u.userId === userId);

            if (userIndex >= 0) {
                const user = faceDatabase.users[userIndex];

                if (!user.descriptorHistory) user.descriptorHistory = user.descriptor ? [user.descriptor] : [];

                user.descriptorHistory.push(...descriptorsToUpdate);
                if (user.descriptorHistory.length > MAX_DESCRIPTOR_HISTORY) {
                    user.descriptorHistory = user.descriptorHistory.slice(-MAX_DESCRIPTOR_HISTORY);
                }

                user.descriptor = averageDescriptors(user.descriptorHistory);
                user.metadata.lastSeen = new Date().toISOString();
                user.metadata.visits = (user.metadata.visits || 0) + 1;

                console.log(`USER UPDATED: ${userId} with ${descriptorsToUpdate.length} new descriptors`);

                await saveDatabaseToFile();

                return {
                    userId: userId,
                    userName: user.userName || 'unknown',
                    isNewUser: false,
                    needsIdentification: !user.userName,
                    distance: resultData.distance,
                    confidence: resultData.confidence,
                    totalVisits: user.metadata.visits
                };
            } else {
                console.error(`User ${userId} not found in database.`);
                return { error: 'User not found in the database.' };
            }
        }
    } catch (error) {
        console.error('Error confirming user identity with descriptor:', {
            message: error.message,
            stack: error.stack,
            userId,
            descriptorsCount: descriptorsToUpdate.length
        });
        return { error: 'Internal server error confirming user identity.' };
    }
}

async function updateUserName(userId, userName) {
    try {
        const userIndex = faceDatabase.users.findIndex(u => u.userId === userId);

        if (userIndex >= 0) {
            const user = faceDatabase.users[userIndex];
            user.userName = userName;
            user.metadata.identifiedAt = new Date().toISOString();
            await saveDatabaseToFile();

            return {
                success: true,
                userId: user.userId,
                userName: user.userName
            };
        }

        return { success: false, error: 'User not found.' };
    } catch (error) {
        console.error('Error updating user name:', error);
        return { success: false, error: 'Internal server error.' };
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
    recognizeFaceWithBatch,
    listAllUsers,
    findUserByName,
    updateUserName,
    debugDatabase,
    getDetectionSessionStats
};