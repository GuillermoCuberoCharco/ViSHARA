const express = require('express');
const { handleSynthesize } = require('../controllers/synthesizeControllers.cjs');

const router = express.Router();
router.post('/', handleSynthesize);

module.exports = router;