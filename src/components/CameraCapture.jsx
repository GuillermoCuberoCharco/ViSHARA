import React, { useEffect, useRef, useState } from 'react';

const CameraCapture = () => {
    const [stream, setStream] = useState(null);
    const videoRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const [chunks, setChunks] = useState([]);
    const [isRecording, setIsRecording] = useState(false);

    useEffect(() => {
        let isMounted = true;
        
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                if (isMounted) {
                    setStream(stream);
                    videoRef.current.srcObject = stream;
                    mediaRecorderRef.current = new MediaRecorder(stream);
                    mediaRecorderRef.current.ondataavailable = event => {
                        setChunks(prev => [...prev, event.data]);
                    };
                    mediaRecorderRef.current.start(1000);
                    setIsRecording(true);
                    console.log('Camera started');
                }
            })
            .catch(err => {
                console.error('Error accessing the camera', err);
                alert('Error accessing the camera: ${err.name} - ${err.message}');
            });


        return () => {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
                mediaRecorderRef.current.stop();
            }
            if (videoRef.current && videoRef.current.srcObject) {
                videoRef.current.srcObject.getTracks().forEach(track => track.stop());
            }
            isMounted = false;
        };
    }, []);

    useEffect(() => {
        console.log('Updating chunks')
        const interval = setInterval(() => {
            console.log('He entrado en el intervalo');
            const blob = new Blob(chunks, { type: 'video/webm' });
            sendVideo(blob);
            setChunks([]);
        }, 1000);
        return () => clearInterval(interval);
    }, [chunks, isRecording]);

    const sendVideo = (blob) => {
        console.log('Sending video');
        const formData = new FormData();
        formData.append('video', blob, 'video.webm');

        fetch('http://localhost:8084/upload', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error sending video');
            }
            console.log('Video sent');
        })
        .catch(error => console.error('Error sending video', error));
    };

    return (
        <div>
            <video ref={videoRef} autoPlay muted />
        </div>
    );
};

export default CameraCapture;
