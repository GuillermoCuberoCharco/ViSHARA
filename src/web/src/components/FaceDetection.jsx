import * as blazeface from '@tensorflow-models/blazeface';
import * as tf from '@tensorflow/tfjs';
import axios from 'axios';
import * as faceapi from 'face-api.js';
import React, { useEffect, useRef, useState } from 'react';
import { SERVER_URL } from '../../src/config';

const FaceDetection = ({ onFaceDetected, onFaceLost, stream }) => {
    // FACE DETECTION REFFERENCES
    const videoRef = useRef(null);
    const modelRef = useRef(null);
    const detectionRef = useRef(null);
    const [isModelLoaded, setIsModelLoaded] = useState(false);
    const [isStreamReady, setIsStreamReady] = useState(false);
    const [isFaceDetected, setIsFaceDetected] = useState(false);

    // FACE RECOGNITION REFFERENCES
    const faceapiModelsRef = useRef(null);
    const lastFaceSentRef = useRef(null);
    const recognizedUserIdRef = useRef(null);

    const loadFaceApiModels = async () => {
        try {
            console.log('Loading Face API models...');

            const MODEL_URL = '../../public/models';

            await Promise.all([
                faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
                faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
                faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL),
            ]);

            faceapiModelsRef.current = true;
            console.log('Face API models loaded successfully');
        } catch (error) {
            console.error('Error loading Face API models:', error);
        }
    };

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

    const extractFacialFeatures = async () => {
        try {
            if (!faceapiModelsRef.current) {
                console.log('Face API models not loaded');
                return;
            }

            const video = videoRef.current;

            const detections = await faceapi.detectSingleFace(video)
                .withFaceLandmarks()
                .withFaceDescriptor();

            if (!detections) {
                console.log('Facial features not detected');
                return null;
            }

            const faceDescriptor = Array.from(detections.descriptor);
            console.log('Facial features extracted:', faceDescriptor);

            return faceDescriptor;
        } catch (error) {
            console.error('Error extracting facial features:', error);
            return null;
        }
    };

    const sendFacialFeaturesToServer = async () => {
        try {
            const now = Date.now();
            if (now - lastFaceSentRef.current < 5000) return;

            lastFaceSentRef.current = now;

            const faceDescriptor = await extractFacialFeatures();
            if (!faceDescriptor) {
                console.log('Facial features not detected in sendFacialFeaturesToServer');
                return;
            }

            const payload = {
                faceDescriptor: faceDescriptor,
                userId: recognizedUserIdRef.current || null
            };

            const response = await axios.post(`${SERVER_URL}/api/recognize-face`, payload);

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
        } catch (error) {
            console.error('Error sending face to server:', error);
        }
    };

    useEffect(() => {
        loadBlazeFaceModels();
        loadFaceApiModels();

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

                    if (faceapiModelsRef.current) {
                        await sendFacialFeaturesToServer();
                    }
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