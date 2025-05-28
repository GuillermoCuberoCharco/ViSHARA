import * as blazeface from '@tensorflow-models/blazeface';
import * as tf from '@tensorflow/tfjs';
import axios from 'axios';
import { useEffect, useRef, useState } from 'react';
import { SERVER_URL } from '../../src/config';
import { useWebSocketContext } from '../contexts/WebSocketContext';

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
    const currentUserIdRef = useRef(null);
    const lastRecognizedUserRef = useRef(null);
    const currentUserDataRef = useRef(null);
    const clientIdRef = useRef(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);

    // CONFIRMATION WINDOW STATE
    const [detectionStatus, setDetectionStatus] = useState('idle'); // idle, collecting, uncertain, confirmed
    const [detectionProgress, setDetectionProgress] = useState({ current: 0, total: 5 });
    const [consensusInfo, setConsensusInfo] = useState(null);

    const consecutiveDetectionsRef = useRef(0);
    const consecutiveLossesRef = useRef(0);
    const lastDetectionTimeRef = useRef(null);
    const recognitionCountRef = useRef(0);

    const { emit } = useWebSocketContext();

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
                scoreThreshold: 0.8
            });

            console.log('BlazeFace model loaded successfully');
            setIsModelLoaded(true);
        } catch (error) {
            console.error('Error loading BlaceFace models:', error);
        }
    };

    const isGoodQuality = (face, video) => {
        const startX = face.topLeft[0];
        const startY = face.topLeft[1];
        const width = face.bottomRight[0] - startX;
        const height = face.bottomRight[1] - startY;

        if (width < 100 || height < 100) return false;

        if (startX < 0 || startY < 0 || startX + width > video.videoWidth || startY + height > video.videoHeight) return false;

        const aspectRatio = width / height;

        if (aspectRatio < 0.7 || aspectRatio > 1.4) return false;

        return true;
    };

    const sendFaceToServer = async (predictions) => {
        try {
            const now = Date.now();
            const sendInterval = currentUserIdRef.current ? 8000 : 3000;

            if (now - lastFaceSentRef.current < sendInterval) return;

            const video = videoRef.current;
            const face = predictions[0];

            if (!isGoodQuality(face, video)) return;

            lastFaceSentRef.current = now;
            recognitionCountRef.current++;

            const canvas = canvasRef.current;
            const ctx = canvas.getContext('2d');

            // FACE COORDINATES
            const startX = face.topLeft[0];
            const startY = face.topLeft[1];
            const width = face.bottomRight[0] - startX;
            const height = face.bottomRight[1] - startY;
            // ADD PADDING TO FACE
            const padding = Math.min(width, height) * 0.2;
            const cropStartX = Math.max(0, startX - padding);
            const cropStartY = Math.max(0, startY - padding);
            const cropWidth = Math.min(width + (padding * 2), video.videoWidth - cropStartX);
            const cropHeight = Math.min(height + (padding * 2), video.videoHeight - cropStartY);

            canvas.width = 200;
            canvas.height = 200;
            ctx.drawImage(video, cropStartX, cropStartY, cropWidth, cropHeight, 0, 0, 200, 200);

            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('face', blob, 'face.jpg');
                formData.append('clientId', clientIdRef.current);

                if (currentUserIdRef.current && currentUserIdRef.current === lastRecognizedUserRef.current) {
                    formData.append('userId', currentUserIdRef.current);
                }

                try {
                    const response = await axios.post(`${SERVER_URL}/api/recognize-face`, formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data',
                            'X-Client-Id': clientIdRef.current
                        }
                    });

                    if (response.data) {
                        handleRecognitionResponse(response.data);
                    }
                } catch (error) {
                    console.error('Error sending face to server:', error);
                    setDetectionStatus('idle');
                    setDetectionProgress({ current: 0, total: 5 });
                }
            }, 'image/jpeg', 0.92);

        } catch (error) {
            console.error('Error sending face to server:', error);
            setDetectionStatus('idle');
        }
    };

    const handleRecognitionResponse = (data) => {
        console.log('Face recognition response:', data);

        if (data.isPreliminary) {
            setDetectionStatus('collecting');
            setDetectionProgress({ current: data.detectionProgress || 0, total: data.totalRequired || 5 });
            console.log(`Collecting data: ${data.detectionProgress}/${data.totalRequired}`);

        } else if (data.isUncertain) {
            setDetectionStatus('uncertain');
            setDetectionProgress({ current: data.detectionProgress || 0, total: data.totalRequired || 5 });
            setConsensusInfo({
                message: 'No clear consensus - continuing to collect data.',
                ration: data.consensusRatio || 0
            });
            console.log(`Uncertain recognition - no consensus reached: ${data.detectionProgress}/${data.totalRequired}`);

        } else if (data.isConfirmed) {
            setDetectionStatus('confirmed');
            setDetectionProgress({ current: data.detectionProgress || 0, total: data.totalRequired || 5 });
            setConsensusInfo({
                message: `Confirmed with ${(data.consensusRatio * 100).toFixed(1)}% consensus`,
                ratio: data.consensusRatio || 1
            });

            const previusUserId = currentUserIdRef.current;
            currentUserIdRef.current = data.userId;
            lastRecognizedUserRef.current = data.userId;

            currentUserDataRef.current = {
                userId: data.userId,
                userName: data.userName,
                isNewUser: data.isNewUser,
                needsIdentification: data.needsIdentification,
                userStatus: data.userStatus
            };

            if (previusUserId !== data.userId || data.needsIdentification) {
                console.log('Notofying message system about confirmed user detection:', data);

                emit('user_detected', {
                    userId: data.userId,
                    userName: data.userName,
                    isNewUser: data.isNewUser,
                    needsIdentification: data.needsIdentification,
                    userStatus: data.userStatus,
                    consensusRatio: data.consensusRatio
                });
            }

            if (data.isNewUser) {
                console.log(`New user confirmed: ${data.userName} (ID: ${data.userId})`);
            } else if (data.needsIdentification) {
                console.log(`User needs identification: (ID: ${data.userId})`);
            } else {
                console.log(`User confirmed: ${data.userName} (ID: ${data.userId})`);
            }
        }
    };

    const resetDetectionState = () => {
        setDetectionStatus('idle');
        setDetectionProgress({ current: 0, total: 5 });
        setConsensusInfo(null);
        currentUserIdRef.current = null;
        lastRecognizedUserRef.current = null;
        currentUserDataRef.current = null;
        recognitionCountRef.current = 0;
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
        if (!stream || !videoRef.current) return;

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
                const now = Date.now();

                if (predictions && predictions.length > 0 && isGoodQuality(predictions[0], video)) {
                    consecutiveDetectionsRef.current++;
                    consecutiveLossesRef.current = 0;
                    lastDetectionTimeRef.current = now;

                    if (!isFaceDetected && consecutiveDetectionsRef.current >= 2) {
                        setIsFaceDetected(true);
                        onFaceDetected();
                    }
                    if (isFaceDetected) {
                        await sendFaceToServer(predictions);
                    }
                } else {
                    consecutiveDetectionsRef.current = 0;
                    consecutiveLossesRef.current++;
                    const timeSinceLastDetection = lastDetectionTimeRef.current ? now - lastDetectionTimeRef.current : Infinity;

                    if (isFaceDetected && consecutiveLossesRef.current >= 3 && timeSinceLastDetection > 10000) {
                        console.log('Face confirmed lost after', consecutiveLossesRef.current, 'losses and ', timeSinceLastDetection, 'ms')
                        setIsFaceDetected(false);
                        onFaceLost();

                        setTimeout(() => {
                            if (!isFaceDetected) {
                                if (currentUserIdRef.current) {
                                    emit('user_lost', {
                                        userId: currentUserIdRef.current
                                    });
                                }
                                resetDetectionState();
                            }
                        }, 3000);
                    }
                }
            } catch (error) {
                console.error('Detection error:', error);
                if (error.message.includes('backend') || error.message.includes('tensor')) {
                    clearInterval(detectionRef.current);
                }
            }
        };

        detectionRef.current = setInterval(detectFace, 1500);

        return () => {
            if (detectionRef.current) {
                clearInterval(detectionRef.current);
            }
        };
    }, [isModelLoaded, stream, onFaceDetected, onFaceLost, isStreamReady, isFaceDetected, emit]);

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