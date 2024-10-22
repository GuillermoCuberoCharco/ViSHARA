import React, { useEffect, useRef, useState } from "react";

const WebSocketVideoComponent = () => {
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const [frameSent, setFramesSent] = useState(0);
    const socketRef = useRef(null);
    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const canvasRef = useRef(null);

    useEffect(() => {
        initializeWebSocket();
        return () => {
            if (socketRef.current) {
                socketRef.current.close();
            }
            if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => track.stop());
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
            socketRef.current = new WebSocket('ws://localhost:8081/video-socket');

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
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
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
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const frame = canvas.toDataURL('image/jpeg', 0.5);
                if (socketRef.current.readyState === WebSocket.OPEN) {
                    socketRef.current.send(JSON.stringify({ type: 'video-frame', frame }));
                    setFramesSent((prev) => prev + 1);
                    if (frameSent % 100 === 0) {
                        console.log("Frames sent:", frameSent);
                    }
                }
            }
            requestAnimationFrame(sendFrame);
        };

        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            sendFrame();
        };
    };

    return (
        <div>
            <h1>WebSocket Video Transmission Status: {connectionStatus}</h1>
            <p>Frames sent: {frameSent}</p>
            <video ref={videoRef} autoPlay playsInline muted style={{ display: 'block', marginBottom: '10px' }}></video>
            <canvas ref={canvasRef} style={{ display: 'none' }}></canvas>
        </div>
    );
};

export default WebSocketVideoComponent;
