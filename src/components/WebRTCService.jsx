import io from "socket.io-client";

let peerConnection;
let socket;

export const initializedWebRTC = async () => {
    socket = io("http://localhost:4000/webrtc");

    const stream = await navigator.mediaDevices.getUserMedia({ video: true });

    peerConnection = new RTCPeerConnection();

    stream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, stream);
    });

    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            socket.emit("ice-candidate", event.candidate);
        }
    };

    // Create and send offer
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    socket.emit("offer", offer);

    // Handle incoming ice candidates and server answers
    socket.on("answer", async (answer) => {
        await peerConnection.setRemoteDescription(answer);
    });

    socket.on("ice-candidate", async (candidate) => {
        await peerConnection.addIceCandidate(candidate);
    });
};