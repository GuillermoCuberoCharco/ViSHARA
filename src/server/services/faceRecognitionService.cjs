const fs = require('fs').promises;
const path = require('path');

function calculateSimilarity(descriptor1, descriptor2) {
    if (!descriptor1 || !descriptor2 || descriptor1.length !== descriptor2.length) {
        return 0;
    }

    let sum = 0;
    for (let i = 0; i < descriptor1.length; i++) {
        const diff = descriptor1[i] - descriptor2[i];
        sum += diff * diff;
    }

    const distance = Math.sqrt(sum);
    const similarity = Math.max(0, 1 - distance / 1.4);

    return similarity;
}

const faceDatabase = {
    nextId: 1,
    users: [],
}

const DB_DIR = path.join(__dirname, '..', 'data');
const DB_FILE = path.join(DB_DIR, 'faceDatabase.json');

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

async function loadDatabaseFromFile() {
    try {
        const data = await fs.readFile(DB_FILE, 'utf-8');
        const loadedDae = JSON.parse(data);

        faceDatabase.nextId = loadedDae.nextId || 1;
        faceDatabase.users = loadedDae.users || [];
        console.log(`Database loaded successfully: ${faceDatabase.users.length} users.`);
    } catch (error) {
        if (error.code !== 'ENOENT') {
            console.error('Error loading database:', error);
        }
    }
}

(async function initialize() {
    await loadDatabaseFromFile();
})();

async function recogniceFace(faceDescriptor, knownUserId = null) {
    try {
        if (!faceDescriptor || !Array.isArray(faceDescriptor)) {
            return { error: 'Invalid face descriptor.' };
        }

        if (knownUserId) {
            const userIndex = faceDatabase.users.findIndex(u => u.userId === knownUserId);
            if (userIndex >= 0) {
                faceDatabase.users[userIndex].descriptor = faceDescriptor;
                faceDatabase.users[userIndex].metadata.lastSeen = new Date().toISOString();
                faceDatabase.users[userIndex].metadata.visits += 1;

                console.log(`User ${knownUserId} updated in the database. (${faceDatabase.users[userIndex].metadata.visits} visits)`);
                await saveDatabaseToFile();
                return { userId: knownUserId, isNewUser: false };
            }
        }

        let bestMatch = null;
        let highestSimilarity = 0;

        for (const user of faceDatabase.users) {
            const similarity = calculateSimilarity(faceDescriptor, user.descriptor);
            // 0.6 is a threshold for similarity for recognition because it is a good balance between accuracy and performance
            if (similarity > 0.6 && similarity > highestSimilarity) {
                highestSimilarity = similarity;
                bestMatch = user;
            }
        }

        if (bestMatch) {
            bestMatch.descriptor = faceDescriptor;
            bestMatch.metadata.lastSeen = new Date().toISOString();
            bestMatch.metadata.visits += 1;
            console.log(`User ${bestMatch.userId} recognized in the database. (Similarity: ${highestSimilarity.toFixed(2)}, ${bestMatch.metadata.visits} visits)`);

            await saveDatabaseToFile();
            return { userId: bestMatch.userId, isNewUser: false, similarity: highestSimilarity };
        } else {
            const newUserId = `user${faceDatabase.nextId++}`;
            const newUser = {
                userId: newUserId,
                descriptor: faceDescriptor,
                metadata: {
                    createdAt: new Date().toISOString(),
                    lastSeen: new Date().toISOString(),
                    visits: 1
                },
            };

            faceDatabase.users.push(newUser);
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

module.exports = {
    recogniceFace,
    listAllUsers
};