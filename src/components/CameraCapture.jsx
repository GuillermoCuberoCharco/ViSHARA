import React, { useEffect, useRef } from 'react';

const CameraCapture = () => {
  const videoRef = useRef(null);

  useEffect(() => {
    const getVideo = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoRef.current.srcObject = stream;
        console.log('Webcam access granted');
      } catch (err) {
        console.error('Error accessing webcam: ', err);
      }
    };

    getVideo();
  }, [videoRef]);

  useEffect(() => {
    const captureAndSendVideo = async () => {
        if (videoRef.current) {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            const video = videoRef.current;

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('file', blob, 'capture.png');

            try {
                const response = await fetch('http://localhost:3000/upload', {
                method: 'POST',
                body: formData
                });
                if (response.ok) {
                const responseText = await response.text();
                console.log('Server response:', responseText);
                } else {
                }
            } catch (error) {
                console.error('Error uploading the video segment:', error);
            }
            }, 'image/jpeg');
        } else {
            console.error('Video element not found');
        }
    };

    const intervalId = setInterval(() => {
        captureAndSendVideo();
    }, 200);

    return () => clearInterval(intervalId);
  }, []);

  return <video ref={videoRef} autoPlay style={{display: 'none'}}/>;
};

export default CameraCapture;

