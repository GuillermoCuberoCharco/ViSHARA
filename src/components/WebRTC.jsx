import { useEffect, useRef } from "react";
import io from "socket.io-client";

const WebRTC = () => {
    const localVideoRef = useRef(null);
    const peerConnectionRef = useRef(null);
    const socketRef = useRef(null);

    useEffect(() => {
        // Configure socket.io for connection
        socketRef.current = io("http://localhost:4000/webrtc");

        // Configure WebRTC connection
        const setupWebRTC = async () => {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            localVideoRef.current.srcObject = stream;

            peerConnectionRef.current = new RTCPeerConnection();

            stream.getTracks().forEach(track => {
                peerConnectionRef.current.addTrack(track, stream);
            });

            peerConnectionRef.current.onicecandidate = event => {
                if (event.candidate) {
                    socketRef.current.emit("ice-candidate", event.candidate);
                }
            };

            // Create and send offer
            const offer = await peerConnectionRef.current.createOffer();
            await peerConnectionRef.current.setLocalDescription(offer);
            socketRef.current.emit("offer", offer);
        };

        setupWebRTC();

        // Handle incoming ice candidates and server answers
        socketRef.current.on("answer", async answer => {
            peerConnectionRef.current.setRemoteDescription(answer);
        });

        socketRef.current.on("ice-candidate", candidate => {
            peerConnectionRef.current.addIceCandidate(candidate);
        });

        return () => {
            socketRef.current.disconnect();
        };
    }, []);

    return (
        <div>
            <video ref={localVideoRef} autoPlay />
        </div>
    );
};

export default WebRTC;