const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const config = require('./environment.cjs');

function setupExpress() {
    const app = express();

    console.log('Configurando CORS con orígenes:', config.cors.origin);

    app.use(cors({
        origin: function (origin, callback) {
            if (!origin) return callback(null, true);

            if (Array.isArray(config.cors.origin)) {
                if (config.cors.origin.indexOf(origin) !== -1) {
                    return callback(null, true);
                }
            } else if (config.cors.origin === '*') {
                return callback(null, true);
            }

            console.log('Origen bloqueado por CORS:', origin);
            callback(new Error('No permitido por CORS'));
        },
        methods: config.cors.methods,
        credentials: config.cors.credentials,
        allowedHeaders: config.cors.allowedHeaders,
        preflightContinue: false,
        optionsSuccessStatus: 204
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
        res.json({
            status: 'ok',
            message: 'Server is running',
            cors: {
                origins: config.cors.origin,
                methods: config.cors.methods
            }
        });
    });

    return app;
}

module.exports = setupExpress;