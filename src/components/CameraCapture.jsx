import React, { useEffect, useRef, useState } from 'react';

const WebcamCapture = () => {
  const webcamRef = useRef(null);
  const wsRef = useRef();
  const mediaRecorderRef = useRef();
  const [isSending, setIsSending] = useState(false);
  const [lastSentMessage, setLastSentMessage] = useState(null);

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ 
      video: { 
        width: {exact: 640}, 
        heigth: {exact: 480}}, 
        audio: false })
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

          let chunks = [];

          mediaRecorderRef.current.ondataavailable = event => {
            if (event.data && event.data.size > 0){
              chunks.push(event.data);
            }
          };
          
          mediaRecorderRef.current.onstop = () => {
            const blob = new Blob(chunks, { type: 'video/webm' });
            if (blob !== lastSentMessage) {
              wsRef.current.send(blob, () => setIsSending(false));
              console.log('Blob sent:', blob.size, 'bytes');
              setLastSentMessage(blob);
            }
            chunks = [];
            if (!isSending) {
              setTimeout(startRecording, 1000);
            }
        };

        const startRecording = () => {
          setIsSending(true);
          chunks = [];
          mediaRecorderRef.current.start();
          setTimeout(() => mediaRecorderRef.current.stop(), 5000);
        };

        startRecording();

        wsRef.current.onerror = error => {
          console.error('WebSocket error:', error);
        };
      }
    });
  }, []);

  return (
    <div className="webcam-capture">
      <video ref={webcamRef} autoPlay playsInline muted></video>
    </div>
  );
};

export default WebcamCapture;