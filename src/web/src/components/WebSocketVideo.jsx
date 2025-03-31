import React, { useEffect, useRef, useState } from "react";

const WebSocketVideoComponent = ({ onStreamReady }) => {
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const [frameSent, setFramesSent] = useState(0);
    const socketRef = useRef(null);
    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const canvasRef = useRef(null);
    const frameRequestRef = useRef(null);
    const frameRate = 15;
    const frameInterval = 1000 / frameRate;
    const lastFrameTimeRef = useRef(0);

    const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8081';

    useEffect(() => {
        if (!canvasRef.current) {
            console.error("Canvas reference is not available");
            return;
        }
        canvasRef.current.width = 320;
        canvasRef.current.height = 240;

        lastFrameTimeRef.current = Date.now();
        initializeWebSocket();
        return () => {
            if (socketRef.current) {
                socketRef.current.close();
            }
            if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => track.stop());
            }
            if (frameRequestRef.current) {
                cancelAnimationFrame(frameRequestRef.current);
            }
        };
    }, []);

    const initializeWebSocket = async () => {
        try {
            console.log("Initializing WebSocket...");
            await setupSocketConnection();
            await setupVideoStream();
            startVideoTransmission();
        } catch (error) {
            console.error("Error initializing WebSocket:", error);
            setConnectionStatus("Error: " + error.message);
        }
    };

    const setupSocketConnection = () => {
        return new Promise((resolve, reject) => {
            socketRef.current = new WebSocket(`${SERVER_URL.replace('/^http', 'ws').replace('/^https', 'wss')}/video-socket`);

            socketRef.current.onopen = () => {
                console.log("WebSocket connected");
                socketRef.current.send(JSON.stringify({ type: 'register', client: 'web' }));
                setConnectionStatus("Connected to server");
                resolve();
            };

            socketRef.current.onerror = (error) => {
                console.error("WebSocket error:", error);
                setConnectionStatus("Connection error");
                reject(error);
            };

            socketRef.current.onclose = (event) => {
                console.log("WebSocket closed:", event.reason);
                setConnectionStatus("Disconnected: " + event.reason);
            };
        });
    };


    const setupVideoStream = async () => {
        try {
            console.log("Setting up video stream...");
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                videoRef.current.play();
            }
            if (onStreamReady) {
                onStreamReady(stream);
            }
            console.log("Video stream set up");
        } catch (error) {
            console.error("Error accessing camera:", error);
            setConnectionStatus("Camera error: " + error.message);
        }
    };

    const startVideoTransmission = () => {
        console.log("Starting video transmission...");
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');
        const video = videoRef.current;

        const sendFrame = () => {
            const now = Date.now();
            const timeDiff = now - lastFrameTimeRef.current;

            if (video.readyState === video.HAVE_ENOUGH_DATA && timeDiff >= frameInterval) {
                canvas.width = video.videoWidth / 2;
                canvas.height = video.videoHeight / 2;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const frame = canvas.toDataURL('image/jpeg', 0.5);
                if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                    socketRef.current.send(JSON.stringify({ type: 'video-frame', frame }));
                    setFramesSent((prev) => prev + 1);
                }
                lastFrameTimeRef.current = now;
            }
            frameRequestRef.current = requestAnimationFrame(sendFrame);
        };

        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth / 2;
            canvas.height = video.videoHeight / 2;
            sendFrame();
        };
    };

    return (
        <div>
            <div style={{
                position: 'fixed',
                bottom: '10px',
                left: '10px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: 'white',
                padding: '5px 10px',
                borderRadius: '5px',
                fontSize: '12px',
                zIndex: 1000
            }}>
                Estado: {connectionStatus} | Frames: {frameSent}
            </div>

            <div style={{ position: 'absolute', opacity: 0.1, pointerEvents: 'none' }}>
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    width="320"
                    height="240"
                />
                <canvas
                    ref={canvasRef}
                    width="320"
                    height="240"
                />
            </div>
        </div>
    );
};

export default WebSocketVideoComponent;