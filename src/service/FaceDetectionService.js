import * as faceapi from 'face-api.js';

class FaceDetectionService {
  constructor() {
    this.isModelLoaded = false;
    this.detectionInterval = null;
  }

  async loadModel() {
    try {
      const MODEL_URL = 'https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights';
      await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
      this.isModelLoaded = true;
      console.log('Face detection model loaded');
    } catch (error) {
      console.error('Error loading face detection model:', error);
      throw error;
    }
  }

  async detectFace(videoElement) {
    if (!this.isModelLoaded || !videoElement) return null;

    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

    try {
      const detection = await faceapi.detectSingleFace(
        canvas,
        new faceapi.TinyFaceDetectorOptions()
      );

      if (detection) {
        const imageDataUrl = canvas.toDataURL('image/jpeg');
        await this.uploadDetection(canvas);
        return imageDataUrl;
      }
    } catch (error) {
      console.error('Error detecting face:', error);
    }

    return null;
  }

  async uploadDetection(canvas) {
    return new Promise((resolve, reject) => {
      canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('file', blob, 'capture.png');

        try {
          const response = await fetch('http://localhost:8081/upload', {
            method: 'POST',
            body: formData
          });

          if (response.ok) {
            const responseText = await response.text();
            console.log('Face detection upload successful:', responseText);
            resolve(responseText);
          } else {
            console.error('Face detection upload failed:', response.status);
            reject(new Error(`Upload failed: ${response.status}`));
          }
        } catch (error) {
          console.error('Error uploading face detection:', error);
          reject(error);
        }
      }, 'image/jpeg');
    });
  }
}

export const faceDetectionService = new FaceDetectionService();