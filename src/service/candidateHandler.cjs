const express = require('express');
const router = express.Router();

let iceCandidates = [];

router.post('/candidates', (req, res) => {
  iceCandidates.push(req.body.candidate);
  res.status(200).end();
});

router.get('/candidates', (req, res) => {
  res.json({ candidates: iceCandidates });
});

module.exports = router;