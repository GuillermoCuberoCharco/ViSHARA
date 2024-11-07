import { useEffect, useRef, useState } from "react";
import { faceDetectionService } from "../service/FaceDetectionService";
import { socketService } from "../service/SocketService";

export const useVideo = (onFaceDetected) => {
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const [framesSent, setFramesSent] = useState(0);
    const [isModelLoaded, setModelLoaded] = useState(false);
    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const canvasRef = useRef(null);
    const frameRequestRef = useRef(null);
    const lastFrameTimeRef = useRef(0);
    const detectionIntervalRef = useRef(null);

    useEffect(() => {
        const initializeFaceDetection = async () => {
            try {
                await faceDetectionService.loadModel();
                setModelLoaded(true);
            } catch (error) {
                console.error("Error loading the model:", error);
            }
        };

        initializeFaceDetection();
    }, []);

    useEffect(() => {
        const setupVideo = async () => {
            try {
                await setupVideoStream();
                socketService.connectVideoSocket();
                startVideoTransmission();
                startFaceDetection();
            } catch (error) {
                console.error("Error setting up video:", error);
                setConnectionStatus(`Error: ${error.message}`);
            }
        };

        setupVideo();

        return () => {
            if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => track.stop());
            }
            if (frameRequestRef.current) {
                cancelAnimationFrame(frameRequestRef.current);
            }
            if (detectionIntervalRef.current) {
                clearInterval(detectionIntervalRef.current);
            }
        };
    }, [isModelLoaded]);

    const setupVideoStream = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true
            });
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
            setConnectionStatus("Connected");
        } catch (error) {
            setConnectionStatus(`Error: ${error.message}`);
            throw error;
        }
    };

    const startVideoTransmission = () => {
        if (!videoRef.current || !canvasRef.current) return;

        const canvas = canvasRef.current;
        const context = canvas.getContext("2d");
        const video = videoRef.current;

        const sendFrame = () => {
            const now = Date.now();
            if (now - lastFrameTime.current >= 66) {
                if (video.readyState === video.HAVE_ENOUGH_DATA) {
                    const scaleFactor = 0.5;
                    canvas.width = video.videoWidth * scaleFactor;
                    canvas.height = video.videoHeight * scaleFactor;

                    context.drawImage(
                        video,
                        0, 0,
                        canvas.width,
                        canvas.height
                    );

                    try {
                        const frame = canvas.toDataURL('image/jpeg', 0.5);
                        socketService.sendVideoFrame(frame);
                        setFramesSent(prev => prev + 1);
                        lastFrameTime.current = now;
                    } catch (error) {
                        console.error('Error sending frame:', error);
                        setConnectionStatus('Error sending frame');
                    }
                }
            } if (videoRef.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const frame = canvas.toDataURL("image/jpeg", 0.8);
                socketService.sendVideoFrame(frame);
                setFramesSent(prev => prev + 1);
            }
            frameRequestRef.current = requestAnimationFrame(sendFrame);
        };

        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            sendFrame();
        };
    };

    const startFaceDetection = () => {
        if (!isModelLoaded || !videoRef.current) return;

        detectionIntervalRef.current = setInterval(async () => {
            const detectionResult = await faceDetectionService.detectFace(videoRef.current);
            if (detectionResult && onFaceDetected) {
                onFaceDetected(detectionResult);
            }
        }, 200);
    };

    return {
        videoRef,
        canvasRef,
        connectionStatus,
        framesSent,
        isModelLoaded
    };
};