require('dotenv').config();

module.exports = {
    port: process.env.PORT || 8081,
    google: {
        credentials: process.env.GOOGLE_APPLICATION_CREDENTIALS,
        clientEmail: process.env.GOOGLE_CLIENT_EMAIL,
        privateKey: process.env.GOOGLE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
        projectId: process.env.GOOGLE_PROJECT_ID
    },
    openai: {
        apiKey: process.env.OPENAI_API_KEY
    },
    cors: {
        origin: true,
        methods: ['GET', 'POST'],
        credentials: true,
        allowedHeaders: ['Content-Type', 'Authorization']
    }
};