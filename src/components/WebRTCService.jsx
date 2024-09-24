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
            socketRef.current = io("http://localhost:4000/webrtc");
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            localStreamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
            console.log("WebRTC initialized");

            peerConnectionRef.current = createPeerConnection();

            localStreamRef.current.getTracks().forEach((track) => {
                peerConnectionRef.current.addTrack(track, localStreamRef.current);
            });
            console.log("Local stream added to peer connection");

            socketRef.current.on("answer", async (answer) => {
                console.log("Received answer:", answer);
                const remoteDesc = new RTCSessionDescription(JSON.parse(answer));
                await peerConnectionRef.current.setRemoteDescription(remoteDesc);
                console.log("Remote description set");
                setConnectionStatus("Connected");
            });

            socketRef.current.on("ice-candidate", async (candidate) => {
                console.log("Received ICE candidate:", candidate);
                try {
                    await peerConnectionRef.current.addIceCandidate(new RTCIceCandidate(JSON.parse(candidate)));
                    console.log("ICE candidate added");
                } catch (error) {
                    console.error("Error adding ICE candidate:", error);
                }
            });

            // Create offer and send it to the server
            const offer = await peerConnectionRef.current.createOffer();
            console.log("Offer created:", offer);
            await peerConnectionRef.current.setLocalDescription(offer);
            console.log("Local description set");
            socketRef.current.emit("offer", JSON.stringify(offer));
            console.log("Offer sent to server");
            setConnectionStatus("Connecting...");

        } catch (error) {
            console.error("Error initializing WebRTC:", error);
            setConnectionStatus("Error: " + error.message);
        }
    };

    const createPeerConnection = () => {
        const pc = new RTCPeerConnection({
            iceServers: [{ urls: "stun:stun.l.google.com:19302", }]
        });

        pc.onicecandidate = (event) => {
            if (event.candidate) {
                console.log("ICE candidate:", event.candidate);
                socketRef.current.emit("ice-candidate", JSON.stringify(event.candidate));
                console.log("ICE candidate sent to server");
            }
        };

        pc.onicecandidatestatechange = () => {
            console.log("ICE candidate state changed to: ", pc.iceConnectionState);
            setConnectionStatus('Ice state: ' + pc.iceConnectionState);
        };

        return pc;
    };

    return (
        <div>
            <h1>WebRTC Connection Status: {connectionStatus}</h1>
            <video ref={videoRef} autoPlay playsInline muted></video>
        </div>
    );
};

export default WebRTCComponent;


