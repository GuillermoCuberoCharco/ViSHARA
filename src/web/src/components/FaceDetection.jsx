import * as blazeface from '@tensorflow-models/blazeface';
import * as tf from '@tensorflow/tfjs';
import axios from 'axios';
import React, { useEffect, useRef, useState } from 'react';

const FaceDetection = ({ onFaceDetected, stream, onNewFaceDetected }) => {
    const videoRef = useRef(null);
    const modelRef = useRef(null);
    const detectionRef = useRef(null);
    const canvasRef = useRef(document.createElement('canvas'));
    const [isModelLoaded, setIsModelLoaded] = useState(false);
    const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8081';

    useEffect(() => {
        const initializeModel = async () => {
            try {
                console.log('Initializing TensorFlow...');
                await tf.ready();
                await tf.setBackend('webgl');
                console.log('TensorFlow initialized with backend:', tf.getBackend());

                console.log('Loading BlazeFace model...');
                modelRef.current = await blazeface.load({
                    maxFaces: 1,
                    inputWidth: 128,
                    inputHeight: 128,
                    iouThreshold: 0.3,
                    scoreThreshold: 0.75
                });

                console.log('BlazeFace model loaded successfully');
                setIsModelLoaded(true);
            } catch (error) {
                console.error('Error during initialization:', error);
            }
        };

        initializeModel();

        return () => {
            if (detectionRef.current) {
                clearInterval(detectionRef.current);
            }
        };
    }, []);

    useEffect(() => {
        if (!stream || !videoRef.current) return;

        const video = videoRef.current;
        video.srcObject = stream;

        video.onloadedmetadata = () => {
            video.play()
                .then(() => console.log('Video playback started'))
                .catch(error => console.error('Video playback error:', error));
        };

        return () => {
            video.srcObject = null;
        };
    }, [stream]);

    const captureFrame = (predictions) => {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);

        const [x, y, width, height] = predictions[0].topLeft.concat(predictions[0].bottomRight);
        const safeX = Math.max(0, x);
        const safeY = Math.max(0, y);
        const safeWidth = Math.min(width, canvas.width - safeX);
        const safeHeight = Math.min(height, canvas.height - safeY);
        const croppedCanvas = document.createElement('canvas');
        const croppedContext = croppedCanvas.getContext('2d');
        croppedCanvas.width = safeWidth;
        croppedCanvas.height = safeHeight;

        croppedContext.drawImage(
            canvas,
            safeX, safeY, safeWidth, safeHeight,
            0, 0, safeWidth, safeHeight
        );
        return croppedCanvas;
    };

    const registerNewFace = async (descriptor, suggestedUserId) => {
        try {
            const label = prompt('Enter your name:');

            if (!label) {
                console.log('User canceled registration');
                return;
            }
            const response = await axios.post(`${SERVER_URL}/register-face`, {
                descriptor,
                userId: suggestedUserId,
                label
            });

            if (response.data.success) {
                console.log('Face registered successfully:', response.data);
                if (onNewFaceDetected) {
                    onNewFaceDetected({
                        userId: suggestedUserId,
                        label
                    });
                }
            }
        } catch (error) {
            console.error('Error registering face:', error);
        }
    };

    const sendFaceToServer = async (canvasElem) => {
        canvasElem.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('frame', blob, 'face.png');
            try {
                const res = await axios.post(`${SERVER_URL}/recognize`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                if (res.data.success) {
                    if (!res.data.isKnownFace) {
                        await registerNewFace(res.data.descriptor, res.data.suggestdUserId);
                    }
                    resolve(res.data);
                } else {
                    reject(new Error(res.data.message));
                }
            } catch (error) {
                console.error('Error sending face to server:', error);
            }
        }, 'image/png');
    };

    useEffect(() => {
        if (!isModelLoaded || !stream || !videoRef.current) {
            console.log('Detection prerequisites not met:', {
                modelLoaded: isModelLoaded,
                streamExists: !!stream,
                videoExists: !!videoRef.current
            });
            return;
        }

        console.log('Starting face detection...');

        const detectFace = async () => {
            if (!videoRef.current || videoRef.current.readyState !== 4) return;

            try {
                const video = videoRef.current;

                if (video.paused || video.ended) return;

                const predictions = await modelRef.current.estimateFaces(video, false);

                if (predictions && predictions.length > 0) {
                    console.log('Face detected:', predictions[0]);
                    onFaceDetected();

                    // Capture frame and send it to server
                    const faceCanvas = captureFrame(predictions);
                    await sendFaceToServer(faceCanvas);
                }
            } catch (error) {
                console.error('Detection error:', error);
                if (error.message.includes('backend') || error.message.includes('tensor')) {
                    clearInterval(detectionRef.current);
                }
            }
        };

        detectionRef.current = setInterval(detectFace, 500);

        return () => {
            if (detectionRef.current) {
                clearInterval(detectionRef.current);
            }
        };
    }, [isModelLoaded, stream, onFaceDetected]);

    return (
        <div style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}>
            <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                width="640"
                height="480"
            />
        </div>
    );
};

export default FaceDetection;