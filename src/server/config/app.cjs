const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const config = require('./environment.cjs');

function setupExpress() {
    const app = express();

    app.use(cors({
        origin: config.cors.origin,
        methods: config.cors.methods,
        credentials: config.cors.credentials,
        allowedHeaders: config.cors.allowedHeaders
    }));

    app.options('*', cors({
        origin: config.cors.origin,
        methods: config.cors.methods,
        credentials: config.cors.credentials,
        allowedHeaders: config.cors.allowedHeaders
    }));

    app.use(bodyParser.json({ limit: '50mb' }));
    app.use(bodyParser.urlencoded({ limit: '50mb', extended: true }));

    // Endpoint de prueba para verificar que el servidor está funcionando
    app.get('/test', (req, res) => {
        res.json({ status: 'ok', message: 'Server is running' });
    });

    return app;
}

module.exports = setupExpress;