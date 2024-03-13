const express = require('express');
const router = express.Router();

let remoteDescription;

router.post('/response', (req, res) => {
  remoteDescription = req.body.sdp;
  res.status(200).end();
});

router.get('/response', (req, res) => {
  res.json({ sdp: remoteDescription });
});

module.exports = router;