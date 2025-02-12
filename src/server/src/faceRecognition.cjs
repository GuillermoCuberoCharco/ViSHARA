require('@tensorflow/tfjs-node');
const faceapi = require('face-api.js');
const path = require('path');
const canvas = require('canvas');
const { Canvas, Image, ImageData } = canvas;

// Simulamos el entorno de navegador para face-api
faceapi.env.monkeyPatch({ Canvas, Image, ImageData });

const MODEL_PATH = path.join(__dirname, '../models');

async function loadModels() {
    await faceapi.nets.tinyFaceDetector.loadFromDisk(MODEL_PATH);
    await faceapi.nets.faceLandmark68Net.loadFromDisk(MODEL_PATH);
    await faceapi.nets.faceRecognitionNet.loadFromDisk(MODEL_PATH);
    console.log('Face-api models loaded (server)');
}
loadModels();

async function recognizeFace(frameBuffer) {
    const img = await canvas.loadImage(frameBuffer);
    const detections = await faceapi
        .detectAllFaces(img, new faceapi.TinyFaceDetectorOptions())
        .withFaceLandmarks()
        .withFaceDescriptors();
    return detections;
}

module.exports = { recognizeFace };
