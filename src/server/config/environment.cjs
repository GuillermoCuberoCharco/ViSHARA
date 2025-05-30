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
            'https://vi-shara.vercel.app',
            'https://vishara.onrender.com',
            'http://localhost:5173'
        ],
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        credentials: true,
        allowedHeaders: [
            'Content-Type',
            'Authorization',
            'X-Client-Id',
            'x-client-id',
            'X-Requested-With',
            'Accept',
            'Origin'
        ],
        exposedHeaders: [
            'X-Total-Count',
            'X-Session-Id'
        ],
        allowEIO3: true,
        pingTimeout: 60000,
        pingInterval: 25000,
        maxAge: 86400
    }
};