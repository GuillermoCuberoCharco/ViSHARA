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
            const wsUrl = SERVER_URL.replace(/^http:\/\//, 'ws://').replace(/^https:\/\//, 'wss://');
            console.log(`Connecting to WebSocket at: ${wsUrl}/video-socket`);

            socketRef.current = new WebSocket(`${wsUrl}/video-socket`);

            const connectionTimeout = setTimeout(() => {
                if (socketRef.current.readyState !== WebSocket.OPEN) {
                    console.error("WebSocket connection timeout");
                    setConnectionStatus("Connection timeout");
                    reject(new Error("WebSocket connection timeout"));
                }
            }, 10000);

            socketRef.current.onopen = () => {
                console.log("WebSocket connected");
                clearTimeout(connectionTimeout);
                socketRef.current.send(JSON.stringify({ type: 'register', client: 'web' }));
                setConnectionStatus("Connected to server");
                resolve();
            };

            socketRef.current.onerror = (error) => {
                console.error("WebSocket error:", error);
                clearTimeout(connectionTimeout);
                setConnectionStatus("Connection error");
                reject(error);
            };

            socketRef.current.onclose = (event) => {
                console.log("WebSocket closed:", event.reason);
                setConnectionStatus("Disconnected: " + event.reason);

                setTimeout(() => {
                    if (socketRef.current?.readyState !== WebSocket.OPEN) {
                        console.log("Attempting to reconnect WebSocket...");
                        setupSocketConnection().catch(err => console.error("Reconnection failed: ", err));
                    }
                }, 5000);
            };
        });
    };

    const setupVideoStream = async () => {
        try {
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
        <div className="hidden">
            <div aria-hidden="true">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    style={{
                        position: 'absolute',
                        width: '1px',
                        height: '1px',
                        padding: 0,
                        margin: '-1px',
                        overflow: 'hidden',
                        clip: 'rect(0, 0, 0, 0)',
                        whiteSpace: 'nowrap',
                        border: 0
                    }}
                />
                <canvas
                    ref={canvasRef}
                    style={{ display: 'none' }}
                />
            </div>
        </div>
    );
};

export default WebSocketVideoComponent;