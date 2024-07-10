// Face Api origin from https://github.com/justadudewhohacks/face-api.js
import * as faceapi from 'face-api.js';
import React, { useEffect, useRef, useState } from 'react';

const CameraCapture = () => {
  const videoRef = useRef(null);
  const [modelIsLoaded, setModelIsLoaded] = useState(false);
  const [faceDetected, setFaceDetected] = useState(false);

  useEffect(() => {
    const loadModel = async () => {
      try {
        const MODEL_URL = 'https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights';
        await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
        setModelIsLoaded(true);
        console.log('Model loaded');
      } catch (error) {
        console.error('Error loading the model:', error);
      }
    };

    loadModel();
  }, []);

  useEffect(() => {
    const getVideo = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoRef.current.srcObject = stream;
        console.log('Webcam access granted');
      } catch (err) {
        console.error('Error accessing webcam: ', err);
      }
    };

    getVideo();
  }, [videoRef]);

  useEffect(() => {
    const captureAndSendVideo = async () => {
      if (videoRef.current) {
        const video = videoRef.current;
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Detect face
        try {
          if (faceapi.nets.tinyFaceDetector.isLoaded) {
            const detection = await faceapi.detectSingleFace(canvas, new faceapi.TinyFaceDetectorOptions());
            const isFaceDetected = !!detection;
            setFaceDetected(isFaceDetected);

            // Send images to server
            canvas.toBlob(async (blob) => {
              const formData = new FormData();
              formData.append('file', blob, 'capture.png');

              try {
                const response = await fetch('http://localhost:3000/upload', {
                  method: 'POST',
                  body: formData
                });
                if (response.ok) {
                  const responseText = await response.text();
                  console.log('Server response:', responseText);
                } else {
                  console.log('Server error:', response.status);
                }
              } catch (error) {
                console.error('Error uploading the video segment:', error);
              }
            }, 'image/jpeg');
          } else {
            console.log('Model not loaded');
          }
        } catch (error) {
          console.error('Error detecting faces:', error);
        }
      }
    };

    const intervalId = setInterval(() => {
      captureAndSendVideo();
    }, 200);

    return () => {
      clearInterval(intervalId);
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach((track) => track.stop());
      }
    };

  }, [modelIsLoaded]);

  console.log('Face detected:', faceDetected);

  return <video ref={videoRef} autoPlay style={{ display: 'none' }} />;
};

export default CameraCapture;

