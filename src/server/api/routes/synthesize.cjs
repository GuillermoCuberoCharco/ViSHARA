const express = require('express');
const { handleSynthesize } = require('../controllers/synthesizeController');

const router = express.Router();
router.post('/', handleSynthesize);

module.exports = router;