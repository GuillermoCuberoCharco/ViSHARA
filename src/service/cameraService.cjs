const express = require('express');
const app = express();
const bodyParser = require('body-parser');
const cors = require("cors");
const fs = require('fs');

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));

app.use(bodyParser.json());

app.use(cors());

const upload = (req, res) => {
    console.log('Received image');
  const image = req.body.image;
  const imageName = `frame_${Date.now()}.jpg`;
  const imagePath = `webrtc_event_logs/${imageName}`;
  const imageBuffer = Buffer.from(image.replace(/^data:image\/\w+;base64,/, ''), 'base64');
  
  fs.writeFile(imagePath, imageBuffer, (err) => {
    if (err) {
      console.error('Error saving image:', err);
      res.status(500).send('Error saving image');
    } else {
      console.log('Image saved:', imageName);
      res.sendStatus(200);
    }
  });
};

module.exports = upload;