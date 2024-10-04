import React, { useEffect, useRef, useState } from "react";
import io from "socket.io-client";

const WebRTCComponent = () => {
    const [connectionStatus, setConnectionStatus] = useState("Disconnected");
    const peerConnectionRef = useRef(null);
    const socketRef = useRef(null);
    const localStreamRef = useRef(null);
    const videoRef = useRef(null);

    useEffect(() => {
        initializeWebRTC();
        return () => {
            // Cleanup
            if (peerConnectionRef.current) {
                peerConnectionRef.current.close();
            }
            if (socketRef.current) {
                socketRef.current.disconnect();
            }
            if (localStreamRef.current) {
                localStreamRef.current.getTracks().forEach((track) => track.stop());
            }
        };
    }, []);

    const initializeWebRTC = async () => {
        try {
            console.log("Initializing WebRTC...");
            await setupSocketConnection();
            await setupLocalStream();
            createPeerConnection();
            createAndSendOffer();
        } catch (error) {
            console.error("Error initializing WebRTC:", error);
            setConnectionStatus("Error: " + error.message);
        }
    };

    const setupSocketConnection = () => {
        return new Promise((resolve, reject) => {
            socketRef.current = io('http://localhost:8081/webrtc', {
                transports: ['websocket'],
                upgrade: false
            });

            socketRef.current.on('connect', () => {
                console.log("Socket connected");
                socketRef.current.emit('register', 'web');
                console.log("Web client registered");
                setConnectionStatus("Connected to server");
                resolve();
            });

            socketRef.current.on('connect_error', (error) => {
                console.error("Connection error:", error);
                setConnectionStatus("Connection error: " + error.message);
                reject(error);
            });

            socketRef.current.on('disconnect', (reason) => {
                console.log("Disconnected: ", reason);
                setConnectionStatus("Disconnected: " + reason);
            });

            socketRef.current.on('answer', handleAnswer);
            socketRef.current.on('ice-candidate', handleIceCandidate);
        });
    };


    const setupLocalStream = async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        localStreamRef.current = stream;
        if (videoRef.current) {
            videoRef.current.srcObject = stream;
        }
        console.log("Local stream set up");
    };

    const createPeerConnection = () => {
        peerConnectionRef.current = new RTCPeerConnection({
            iceServers: [
                //{ urls: "stun:stun.l.google.com:19302", }
            ]
        });

        peerConnectionRef.current.onicecandidate = (event) => {
            if (event.candidate) {
                console.log("ICE candidate:", event.candidate);
                socketRef.current.emit('ice-candidate', event.candidate);
            }
        };

        peerConnectionRef.current.oniceconnectionstatechange = () => {
            console.log("ICE connection state changed to: ", peerConnectionRef.current.iceConnectionState);
            setConnectionStatus('Ice state: ' + peerConnectionRef.current.iceConnectionState);
        };

        peerConnectionRef.current.onconnectionstatechange = () => {
            console.log("Connection state changed to: ", peerConnectionRef.current.connectionState);
            setConnectionStatus('Connection state: ' + peerConnectionRef.current.connectionState);
        };

        localStreamRef.current.getTracks().forEach((track) => {
            peerConnectionRef.current.addTrack(track, localStreamRef.current);
        });
        console.log("Local stream added to peer connection");
    };

    const createAndSendOffer = async () => {
        try {
            if (!peerConnectionRef.current) {
                throw new Error("Peer connection not initialized");
            }
            const offer = await peerConnectionRef.current.createOffer();
            await peerConnectionRef.current.setLocalDescription(offer);
            console.log("Offer created: ", offer);
            socketRef.current.emit('offer', { type: offer.type, sdp: offer.sdp });
            console.log("Offer sent to server");
        } catch (error) {
            console.error("Error creating offer:", error);
        }
    };

    const handleAnswer = async (answer) => {
        try {
            if (!peerConnectionRef.current) {
                throw new Error("Peer connection not initialized");
            }
            console.log("Answer received: ", answer);
            await peerConnectionRef.current.setRemoteDescription(new RTCSessionDescription(answer));
            console.log("Remote description set");
        } catch (error) {
            console.error("Error setting remote description:", error);
        }
    };

    const handleIceCandidate = async (candidate) => {
        try {
            if (!peerConnectionRef.current) {
                throw new Error("Peer connection not initialized");
            }
            console.log("ICE candidate received: ", candidate);
            await peerConnectionRef.current.addIceCandidate(new RTCIceCandidate(candidate));
            console.log("ICE candidate added");
        } catch (error) {
            console.error("Error adding ICE candidate:", error);
        }
    };

    return (
        <div>
            <h1>WebRTC Connection Status: {connectionStatus}</h1>
            <video ref={videoRef} autoPlay playsInline muted></video>
        </div>
    );
};

export default WebRTCComponent;


