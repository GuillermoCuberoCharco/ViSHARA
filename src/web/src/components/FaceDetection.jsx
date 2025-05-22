import * as blazeface from '@tensorflow-models/blazeface';
import * as tf from '@tensorflow/tfjs';
import axios from 'axios';
import React, { useEffect, useRef, useState } from 'react';
import { SERVER_URL } from '../../src/config';

const FaceDetection = ({ onFaceDetected, onFaceLost, stream }) => {
    // FACE DETECTION REFERENCES
    const videoRef = useRef(null);
    const modelRef = useRef(null);
    const detectionRef = useRef(null);
    const [isModelLoaded, setIsModelLoaded] = useState(false);
    const [isStreamReady, setIsStreamReady] = useState(false);
    const [isFaceDetected, setIsFaceDetected] = useState(false);

    // FACE RECOGNITION REFFERENCES
    const canvasRef = useRef(document.createElement('canvas'));
    const lastFaceSentRef = useRef(null);
    const recognizedUserIdRef = useRef(null);

    const loadBlazeFaceModels = async () => {
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
            console.error('Error loading BlaceFace models:', error);
        }
    };

    const sendFaceToServer = async (predictions) => {
        try {
            const now = Date.now();
            if (now - lastFaceSentRef.current < 5000) return;

            lastFaceSentRef.current = now;

            const video = videoRef.current;
            const canvas = canvasRef.current;
            const ctx = canvas.getContext('2d');

            // FACE COORDINATES
            const face = predictions[0];
            const startX = face.topLeft[0];
            const startY = face.topLeft[1];
            const width = face.bottomRight[0] - startX;
            const height = face.bottomRight[1] - startY;
            // ADD PADDING TO FACE
            const padding = Math.min(width, height) * 0.2;
            const cropStartX = Math.max(0, startX - padding);
            const cropStartY = Math.max(0, startY - padding);
            const cropWidth = width + (padding * 2);
            const cropHeight = height + (padding * 2);

            ctx.drawImage(video, cropStartX, cropStartY, cropWidth, cropHeight, 0, 0, 150, 150);

            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('face', blob, 'face.jpg');

                if (recognizedUserIdRef.current) {
                    formData.append('userId', recognizedUserIdRef.current);
                }

                const response = await axios.post(`${SERVER_URL}/api/recognize-face`, formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                });

                if (response.data && response.data.userId) {
                    const isNewUser = response.data.isNewUser;

                    if (isNewUser) {
                        console.log('New user detected:', response.data.userId);
                    } else if (!recognizedUserIdRef.current) {
                        console.log('Recognized user with ID:', response.data.userId);
                    } else if (recognizedUserIdRef.current !== response.data.userId) {
                        console.log('User switched from', recognizedUserIdRef.current, 'to', response.data.userId);
                    }

                    recognizedUserIdRef.current = response.data.userId;
                }
            }, 'image/jpeg', 0.8);

        } catch (error) {
            console.error('Error sending face to server:', error);
        }
    };

    useEffect(() => {
        loadBlazeFaceModels();

        return () => {
            if (detectionRef.current) {
                clearInterval(detectionRef.current);
            }
        };
    }, []);

    useEffect(() => {
        if (!stream || !videoRef.current) {
            console.log('Detection prerequisites not met');
            return;
        }

        console.log('Setting up video stream...');

        const video = videoRef.current;
        video.srcObject = stream;

        video.onloadedmetadata = () => {
            video.play()
                .then(() => {
                    console.log('Video playback started');
                    setIsStreamReady(true);
                })
                .catch(error => console.error('Video playback error:', error));
        };

        return () => {
            setIsStreamReady(false);
            video.srcObject = null;
        };
    }, [stream]);

    useEffect(() => {
        if (!isModelLoaded || !isStreamReady || !videoRef.current) return;

        const detectFace = async () => {
            if (!videoRef.current || videoRef.current.readyState !== 4) return;

            try {
                const video = videoRef.current;

                if (video.paused || video.ended) return;

                const predictions = await modelRef.current.estimateFaces(video, false);

                if (predictions && predictions.length > 0) {
                    if (!isFaceDetected) {
                        setIsFaceDetected(true);
                        onFaceDetected();
                    }

                    await sendFaceToServer(predictions);
                } else {
                    if (isFaceDetected) {
                        setIsFaceDetected(false);
                        onFaceLost();
                        recognizedUserIdRef.current = null;
                    }
                }
            } catch (error) {
                console.error('Detection error:', error);
                if (error.message.includes('backend') || error.message.includes('tensor')) {
                    clearInterval(detectionRef.current);
                }
            }
        };

        detectionRef.current = setInterval(detectFace, 5000);

        return () => {
            if (detectionRef.current) {
                clearInterval(detectionRef.current);
            }
        };
    }, [isModelLoaded, stream, onFaceDetected, onFaceLost, isStreamReady, isFaceDetected]);

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