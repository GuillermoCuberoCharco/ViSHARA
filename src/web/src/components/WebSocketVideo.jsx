import { useEffect, useRef, useState } from "react";
import io from "socket.io-client";
import { SERVER_URL } from "../config";

const WebSocketVideoComponent = ({ onStreamReady, onStreamError }) => {
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const [frameSent, setFramesSent] = useState(0);
    const socketRef = useRef(null);
    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const canvasRef = useRef(null);
    const frameRequestRef = useRef(null);
    const isTransmitting = useRef(false);
    const frameRate = 15;
    const frameInterval = 1000 / frameRate;
    const lastFrameTimeRef = useRef(0);

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
                socketRef.current.disconnect();
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
            console.log(`Connecting to Socket.IO at: ${SERVER_URL}(path: /video-socket)`);

            socketRef.current = io(SERVER_URL, {
                path: '/video-socket',
                transports: ['websocket', 'polling'],
                reconnectionAttempts: 5,
                reconnectionDelay: 1000,
                timeout: 10000
            });

            socketRef.current.on('connect', () => {
                console.log("Connected to Socket.IO");
                socketRef.current.emit('register', { client: 'web' })
                setConnectionStatus("Connected");
                resolve();
            });

            socketRef.current.on('connect_error', (error) => {
                console.error("Socket.IO connection error:", error);
                setConnectionStatus("Socket.IO error: " + error.message);
                reject(error);
            });

            socketRef.current.on('disconnect', () => {
                console.log("Disconnected from Socket.IO");
                setConnectionStatus("Disconnected");
            });

            const connectionTimeout = setTimeout(() => {
                console.error("Socket.IO connection timeout");
                setConnectionStatus("Connection timeout");
                reject(new Error("Socket.IO connection timeout"));
            }, 10000);

            socketRef.current.on('connect', () => {
                clearTimeout(connectionTimeout);
            });
        });
    };


    const setupVideoStream = async () => {
        try {
            console.log("Setting up video stream...");
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                await videoRef.current.play();
                console.log("Video stream playing");
            }
            if (onStreamReady) {
                onStreamReady(stream);
            }
            console.log("Video stream set up");
            return stream;
        } catch (error) {
            console.error("Error accessing camera:", error);

            if (onStreamError) {
                onStreamError(error);
            }

            if (error.name === 'NotAllowedError') {
                setConnectionStatus("Error: Camera access denied");
            } else if (error.name === 'NotFoundError') {
                setConnectionStatus("Error: Camera not found");
            } else if (error.name === 'NotReadableError') {
                setConnectionStatus("Error: Camera not readable");
            } else {
                setConnectionStatus("Error: Camera " + error.message);
            }
            if (onStreamReady) {
                onStreamReady(null);
            }
        }
    };

    const startVideoTransmission = () => {
        console.log("Starting video transmission...");
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');
        const video = videoRef.current;

        isTransmitting.current = true;

        const sendFrame = () => {
            if (!isTransmitting.current) { console.log("Transmision stopped"); return; }

            const now = Date.now();
            const timeDiff = now - lastFrameTimeRef.current;

            if (video.readyState === video.HAVE_ENOUGH_DATA && timeDiff >= frameInterval) {
                canvas.width = video.videoWidth / 2;
                canvas.height = video.videoHeight / 2;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const frame = canvas.toDataURL('image/jpeg', 0.5);
                if (socketRef.current && socketRef.current.connected) {
                    socketRef.current.emit('video_frame', {
                        type: 'video-frame',
                        frame: frame
                    });
                    setFramesSent((prev) => prev + 1);
                }
                lastFrameTimeRef.current = now;
            }
            frameRequestRef.current = requestAnimationFrame(sendFrame);
        };

        if (video.readyState >= 3) {
            sendFrame();
        } else {
            video.onloadedmetadata = () => {
                canvas.width = video.videoWidth / 2;
                canvas.height = video.videoHeight / 2;
                sendFrame();
            };
        }
    };

    return (
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
    );
};

export default WebSocketVideoComponent;