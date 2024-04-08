import axios from 'axios';
import React, { useEffect, useRef } from 'react';

const WebcamCapture = () => {
  const webcamRef = useRef(null);
  const peerRef = useRef();

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      .then(stream => {
        webcamRef.current.srcObject = stream;
        
        const configuration = {
          iceServers: [
            {
              urls: 'turn:localhost:3478',
              username: 'username',
              credential: 'password'
            }
          ]
        }
        peerRef.current = new RTCPeerConnection(configuration);

        stream.getTracks().forEach(track => peerRef.current.addTrack(track, stream));

        peerRef.current.onicecandidate = event => {
          if (event.candidate) {
            axios.post('http://localhost:8082/candidates', { candidate: event.candidate })
              .then(() => console.log('ICE candidate sent to server.'))
              .catch(error => console.error('Error sending ICE candidate to server:', error));
          }
        };

        peerRef.current.onicegatheringstatechange = () => {
          if (peerRef.current.iceGatheringState === 'complete') {
            axios.post('http://localhost:8082/response', { sdp: peerRef.current.localDescription })
              .then(() => console.log('Local description sent to server.'))
              .catch(error => console.error('Error sending local description to server:', error));
          }
        };

        peerRef.current.onnegotiationneeded = () => {
          peerRef.current.createOffer().then(offer => {
            return peerRef.current.setLocalDescription(offer);
          }).then(() => {
            axios.post('http://localhost:8082/upload', { sdp: peerRef.current.localDescription })
              .then(() => console.log('Local description sent to server.'))
              .catch(error => console.error('Error sending local description to server:', error));
          });
        };

        axios.get('http://localhost:8082/response')
          .then(response => {
            const remoteDescription = new RTCSessionDescription(response.data.sdp);
            peerRef.current.setRemoteDescription(remoteDescription);
          })
          .catch(error => console.error('Error getting response from server:', error));

        axios.get('http://localhost:8082/candidates')
          .then(response => {
            response.data.candidates.forEach(candidateInfo => {
              const candidate = new RTCIceCandidate(candidateInfo);
              peerRef.current.addIceCandidate(candidate);
            });
          })
          .catch(error => console.error('Error getting ICE candidates from server:', error));
      });
  }, []);

  return (
    <div className="webcam-capture">
      <video ref={webcamRef} autoPlay playsInline muted></video>
    </div>
  );
};

export default WebcamCapture;