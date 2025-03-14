const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const config = require('./environment.cjs');

function setupExpress() {
    const app = express();

    app.use(cors(config.cors));
    app.use(bodyParser.json());
    app.use(bodyParser.urlencoded({ extended: true }));

    return app;
}

module.exports = setupExpress;