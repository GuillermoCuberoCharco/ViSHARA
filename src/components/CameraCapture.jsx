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
          if (MediaRecorder.isTypeSupported('video/webm;codecs=vp9')) {
            console.log('WebM format is supported')
            mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp9' });
          } else {
            console.error('WebM format is not supported');
          }
          mediaRecorderRef.current.ondataavailable = event => {
            
            if (event.data && event.data.size > 1){
              wsRef.current.send(event.data);
            }
          };
          mediaRecorderRef.current.start(33); 
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