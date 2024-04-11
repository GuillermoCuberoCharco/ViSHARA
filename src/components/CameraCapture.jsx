import React, { useEffect, useRef } from 'react';

const WebcamCapture = () => {
  const webcamRef = useRef(null);
  const wsRef = useRef();
  const mediaRecorderRef = useRef();

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      .then(stream => {
        webcamRef.current.srcObject = stream;

        wsRef.current = new WebSocket('ws://localhost:8084');

        wsRef.current.onopen = () => {
          mediaRecorderRef.current = new MediaRecorder(stream);
          mediaRecorderRef.current.ondataavailable = event => {
            wsRef.current.send(event.data);
          };
          mediaRecorderRef.current.start(100); 
        };

        wsRef.current.onerror = error => {
          console.error('WebSocket error:', error);
        };
      });
  }, []);

  return (
    <div className="webcam-capture">
      <video ref={webcamRef} autoPlay playsInline muted></video>
    </div>
  );
};

export default WebcamCapture;