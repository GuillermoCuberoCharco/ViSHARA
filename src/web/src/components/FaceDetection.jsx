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
        console.log('Frame captured');
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
            }, {
                headers: { 'Content-Type': 'application/json' },
                withCredentials: true
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

    const compressImage = async (canvas, quality = 0.7) => {
        return new Promise((resolve) => {
            canvas.toBlob((blob) => resolve(blob), 'image/jpeg', quality);
        });
    };

    const retryOperation = async (operation, maxRetries = 3, delay = 1000) => {
        console.log(`Starting retry operation with ${maxRetries} max retries...`);
        for (let i = 0; i < maxRetries; i++) {
            try {
                console.log(`Attempt ${i + 1}/${maxRetries}`);
                return await operation();
            } catch (error) {
                console.log(`Attempt ${i + 1} failed:`, error.message);
                if (i === maxRetries - 1) throw error;
                console.log(`Retry ${i + 1}/${maxRetries} afer error:`, error.message);
                await new Promise((resolve) => setTimeout(resolve, delay));
            }
        }
    };

    const sendFaceToServer = async (canvasElem) => {
        console.log('Starting sendFaceToServer...');
        try {
            const result = await retryOperation(async () => {
                console.log('Compressing image...');
                const compressedBlob = await compressImage(canvasElem);

                console.log('Creating form data...');
                const formData = new FormData();
                formData.append('frame', compressedBlob, 'face.png');

                console.log('Sending request to server...');
                // const res = await axios.post(`${SERVER_URL}/recognize`, formData, {
                //     headers: { 'Content-Type': 'multipart/form-data' },
                //     withCredentials: true,
                //     timeout: 15000,
                //     maxContentLength: 5000000,
                //     maxBodyLength: 5000000
                // });

                // console.log('Server response received:', res.data);
                // if (res.data.success) {
                //     if (!res.data.isKnownFace) {
                //         console.log('New face detected, registering...');
                //         await registerNewFace(res.data.descriptor, res.data.suggestedUserId);
                //     }
                //     return res.data;
                // } else {
                //     throw new Error(res.data.message);
                // }
            }, 3, 1000);

            return result;
        } catch (error) {
            console.error('Error in sendFaceToServer:', error);
            throw error;
        }
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

        let isProcessing = false;
        let processingTimeout

        const detectFace = async () => {
            if (!videoRef.current || videoRef.current.readyState !== 4 || isProcessing) return;

            try {
                isProcessing = true;
                console.log('Starting face detection...');

                const video = videoRef.current;
                const predictions = await modelRef.current.estimateFaces(video, false);

                if (predictions && predictions.length > 0) {
                    console.log('Face detected, attempting recognition...');
                    const faceCanvas = captureFrame(predictions);
                    const recognitionPrimise = sendFaceToServer(faceCanvas);
                    const timeoutPromise = new Promise((_, reject) =>
                        setTimeout(() => reject(new Error('Face recognition timeout')), 10000)
                    );
                    try {
                        const result = await Promise.race([recognitionPrimise, timeoutPromise]);
                        console.log('Recognition result:', result);
                        if (result && result.success) {
                            console.log('Face recognition successfull');
                            onFaceDetected(result);
                        }
                    } catch (regonitionError) {
                        console.error('Recognition error:', regonitionError);
                    }
                }
            } catch (error) {
                console.error('Detection error:', error);
            } finally {
                isProcessing = false;
            }
        };

        detectionRef.current = setInterval(detectFace, 3000);

        return () => {
            if (detectionRef.current) clearInterval(detectionRef.current);
            if (processingTimeout) clearTimeout(processingTimeout);
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