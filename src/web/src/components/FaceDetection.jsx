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

    // FACE RECOGNITION REFFERENCES WITH BATCH COLLECTION
    const batchCollectionRef = useRef({
        frames: [],
        isCollecting: false,
        sessionId: null,
        currentUserId: null
    });
    const canvasRef = useRef(document.createElement('canvas'));
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
                scoreThreshold: 0.75
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

        if (width < 120 || height < 120) {
            console.log(`Face too small: ${width}x${height} (minimum 120x120)`);
            return false;
        }

        if (startX < 0 || startY < 0 || startX + width > video.videoWidth || startY + height > video.videoHeight) return false;

        const aspectRatio = width / height;

        if (aspectRatio < 0.6 || aspectRatio > 1.6) return false;

        return true;
    };

    const startBatchCollection = (predictions) => {
        const batch = batchCollectionRef.current;

        if (batch.isCollecting) return;

        console.log('Starting batch collection for face recognition');
        batch.isCollecting = true;
        batch.frames = [];
        batch.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        setDetectionStatus('collecting');
        setDetectionProgress({ current: 0, total: 5 });

        addFrameToBatch(predictions[0]);
    };

    const addFrameToBatch = async (face) => {
        const batch = batchCollectionRef.current;
        if (!batch.isCollecting || batch.frames.length >= 5) return;

        try {
            const video = videoRef.current;
            const canvas = canvasRef.current;
            const ctx = canvas.getContext('2d');

            // FACE COORDINATES
            const startX = face.topLeft[0];
            const startY = face.topLeft[1];
            const width = face.bottomRight[0] - startX;
            const height = face.bottomRight[1] - startY;
            // ADD PADDING TO FACE
            const padding = Math.min(width, height) * 0.4;
            const cropStartX = Math.max(0, startX - padding);
            const cropStartY = Math.max(0, startY - padding);
            const cropWidth = Math.min(width + (padding * 2), video.videoWidth - cropStartX);
            const cropHeight = Math.min(height + (padding * 2), video.videoHeight - cropStartY);

            canvas.width = 400;
            canvas.height = 400;
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(video, cropStartX, cropStartY, cropWidth, cropHeight, 0, 0, canvas.width, canvas.height);

            canvas.toBlob(async (blob) => {
                if (blob && batch.isCollecting) {
                    const arrayBuffer = await blob.arrayBuffer();
                    batch.frames.push(new Uint8Array(arrayBuffer));
                    const currentCount = batch.frames.length;
                    console.log(`Frame added to batch: ${currentCount}/5`);
                    setDetectionProgress({ current: currentCount, total: 5 });

                    if (currentCount >= 5) await processBatch();
                }
            }, 'image/jpeg', 0.98);
        } catch (error) {
            console.error('Error adding frame to batch:', error);
        }
    };

    const processBatch = async () => {
        const batch = batchCollectionRef.current;

        if (!batch.isCollecting || batch.frames.length < 5) return;

        try {
            console.log('Processing batch of 5 frames...');
            setDetectionStatus('processing');

            const formData = new FormData();

            batch.frames.forEach((frameBuffer, index) => {
                const blob = new Blob([frameBuffer], { type: 'image/jpeg' });
                formData.append('faces', blob, `face_${index}.jpg`);
            });

            formData.append('clientId', clientIdRef.current);
            formData.append('sessionId', batch.sessionId);

            if (currentUserIdRef.current) formData.append('userId', currentUserIdRef.current);

            const response = await axios.post(`${SERVER_URL}/api/recognize-face`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'X-Client-Id': clientIdRef.current
                },
                timeout: 15000
            });

            if (response.data) handleBatchRecognitionResponse(response.data);
        } catch (error) {
            console.error('Error processing batch:', error);
            resetBatchCollection();
            setDetectionStatus('idle');
        }
    };

    const handleBatchRecognitionResponse = (data) => {
        console.log('Batch recognition response:', data);

        const batch = batchCollectionRef.current;

        if (data.isUncertain) {
            setDetectionStatus('uncertain');
            setConsensusInfo({
                message: `No clear consensus reached (${(data.consensusRatio * 100).toFixed(1)}% agreement)`,
                ratio: data.consensusRatio
            });
            console.log('Uncertain recognition result:', data);

        } else if (data.isConfirmed) {
            setDetectionStatus('confirmed');
            setConsensusInfo({
                message: `Confirmed with ${(data.consensusRatio * 100).toFixed(1)}% consensus`,
                ratio: data.consensusRatio
            });

            const previousUserId = currentUserIdRef.current;
            currentUserIdRef.current = data.userId;
            lastRecognizedUserRef.current = data.userId;

            currentUserDataRef.current = {
                userId: data.userId,
                userName: data.userName,
                isNewUser: data.isNewUser,
                needsIdentification: data.needsIdentification,
                userStatus: data.userStatus || 'confirmed'
            };

            if (previousUserId !== data.userId || data.needsIdentification) {
                console.log('New user recognized:', currentUserDataRef.current);

                emit('user_detected', {
                    userId: data.userId,
                    userName: data.userName,
                    isNewUser: data.isNewUser,
                    needsIdentification: data.needsIdentification,
                    userStatus: data.userStatus || 'confirmed',
                    consensusRatio: data.consensusRatio
                });
            }

            if (data.isNewUser) {
                console.log(`🆕 New user confirmed: ${data.userName} (ID: ${data.userId})`);
            } else if (data.needsIdentification) {
                console.log(`❓ User needs identification: (ID: ${data.userId})`);
            } else {
                console.log(`✅ User confirmed: ${data.userName} (ID: ${data.userId})`);
            }
        }

        resetBatchCollection();
    };

    const resetBatchCollection = () => {
        const batch = batchCollectionRef.current;
        batch.isCollecting = false;
        batch.frames = [];
        batch.sessionId = null;
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
                        const batch = batchCollectionRef.current;
                        if (!batch.isCollecting && detectionStatus === 'idle') {
                            startBatchCollection(predictions);
                        } else if (batch.isCollecting && batch.frames.length < 5) {
                            addFrameToBatch(predictions[0]);
                        }
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

        detectionRef.current = setInterval(detectFace, 2000);

        return () => {
            if (detectionRef.current) {
                clearInterval(detectionRef.current);
            }
        };
    }, [isModelLoaded, stream, onFaceDetected, onFaceLost, isStreamReady, isFaceDetected, emit, detectionStatus]);

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