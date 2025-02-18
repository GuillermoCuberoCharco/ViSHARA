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
            canvas.toBlob((blob) => resolve(blob), 'image/png', quality);
        });
    };

    const retryOperation = async (operation, maxRetries = 3, delay = 1000) => {
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await operation();
            } catch (error) {
                if (i === maxRetries - 1) throw error;
                console.log(`Retry ${i + 1}/${maxRetries} afer error:`, error.message);
                await new Promise((resolve) => setTimeout(resolve, delay));
            }
        }
    };

    const sendFaceToServer = async (canvasElem) => {
        return new Promise((resolve, reject) => {
            retryOperation(async () => {
                const compressedBlob = await compressImage(canvasElem);
                const formData = new FormData();
                formData.append('frame', compressedBlob, 'face.png');
                try {
                    const res = await axios.post(`${SERVER_URL}/recognize`, formData, {
                        headers: { 'Content-Type': 'multipart/form-data' },
                        withCredentials: true,
                        timeout: 15000,
                        maxContentLength: 10000000,
                        maxBodyLength: 10000000
                    });

                    if (res.data.success) {
                        if (!res.data.isKnownFace) {
                            try {
                                await registerNewFace(res.data.descriptor, res.data.suggestdUserId);
                                resolve(res.data);
                            } catch (regError) {
                                console.error('Error registering new face:', regError);
                                reject(regError);
                            }
                        } else {
                            resolve(res.data);
                        }
                    } else {
                        reject(new Error(res.data.message));
                    }
                } catch (error) {
                    console.error('Error sending face to server:', error);
                    reject(error);
                }
            }, 'image/png');
        });
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
        let isProcessing = false;

        const detectFace = async () => {
            if (!videoRef.current || videoRef.current.readyState !== 4 || isProcessing) return;

            try {
                isProcessing = true;
                const video = videoRef.current;

                if (video.paused || video.ended) {
                    isProcessing = false;
                    return;
                }

                const predictions = await modelRef.current.estimateFaces(video, false);

                if (predictions && predictions.length > 0) {
                    console.log('Face detected:', predictions[0]);
                    onFaceDetected();

                    const faceCanvas = captureFrame(predictions);
                    try {
                        const result = await sendFaceToServer(faceCanvas);
                        console.log('Face recognition result:', result);
                    } catch (error) {
                        console.error('Face recognition error:', error);
                    }
                }
            } catch (error) {
                console.error('Detection error:', error);
                if (error.message.includes('backend') || error.message.includes('tensor')) {
                    clearInterval(detectionRef.current);
                }
            } finally {
                isProcessing = false;
            }
        };

        let processingTimeout;
        detectionRef.current = setInterval(() => {
            if (processingTimeout) clearTimeout(processingTimeout);
            processingTimeout = setTimeout(detectFace, 500);
        }, 2000);

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