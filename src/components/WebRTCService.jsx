import io from "socket.io-client";

let peerConnection;
let socket;
let localStream;

const createPeerConnection = () => {
    const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }] // Google's public STUN server
    });

    pc.onicecandidate = (event) => {
        if (event.candidate) {
            console.log("Sending ICE candidate to the other peer");
            socket.emit("ice-candidate", JSON.stringify(event.candidate));
        }
    };

    pc.oniceconnectionstatechange = () => {
        console.log("ICE connection state changed to: ", pc.iceConnectionState);
    };

    pc.onicegatheringstatechange = () => {
        console.log("ICE gathering state changed to: ", pc.iceGatheringState);
    };

    return pc;
};

export const initializedWebRTC = async () => {
    try {
        console.log("Initializing WebRTC");
        socket = io("http://localhost:4000/webrtc");
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        localStream = stream;
        console.log("Local stream created");

        peerConnection = createPeerConnection();

        localStream.getTracks().forEach((track) => {
            peerConnection.addTrack(track, localStream);
        });
        console.log("Local stream added to peer connection");

        socket.on("answer", async (answer) => {
            console.log("Answer received:", answer);
            const remoteDesc = new RTCSessionDescription(JSON.parse(answer));
            await peerConnection.setRemoteDescription(remoteDesc);
            console.log("Remote description set");
        });

        socket.on("ice-candidate", async (candidate) => {
            console.log("ICE candidate received:", candidate);
            try {
                await peerConnection.addIceCandidate(new RTCIceCandidate(JSON.parse(candidate)));
                console.log("ICE candidate added");
            } catch (error) {
                console.error("Error adding ICE candidate:", error);
            }
        });

        // Create offer and send it to the other peer
        const offer = await peerConnection.createOffer();
        console.log("Offer created:", offer);
        await peerConnection.setLocalDescription(offer);
        console.log("Local description set");
        socket.emit("offer", JSON.stringify(offer));
        console.log("Offer sent");

        console.log("WebRTC initialized and offer sent");

    } catch (error) {
        console.log("Error during WebRTC initialized: ", error);
    }
};