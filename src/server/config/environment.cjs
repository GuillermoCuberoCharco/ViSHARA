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
        origin: [
            process.env.FRONTEND_URL,
            'http://localhost:5173'
        ],
        methods: ['GET', 'POST'],
        credentials: true,
        allowedHeaders: ['Content-Type', 'Authorization'],
        allowEIO3: true,
        pingTimeout: 60000,
        pingInterval: 25000
    }
};