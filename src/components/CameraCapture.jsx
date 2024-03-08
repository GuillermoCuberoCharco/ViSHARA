import axios from 'axios';
import React, { useRef, useState } from 'react';
import Webcam from 'react-webcam';

const WebcamCapture = () => {
  const webcamRef = useRef(null);
  const [imgSrc, setImgSrc] = useState("");
  const [ intervalId, setIntervalId ] = useState(null);

  const capture = async () => {
    const imageSrc = webcamRef.current.getScreenshot();

    try {
      await axios.post('http://localhost:8082/upload', { image: imageSrc });
      console.log('Image sent to server.');
      setImgSrc(imageSrc);
    } catch (error) {
      console.error('Error sending image to server:', error);
    }
  };

  const startCapture = () => {
    const interval = setInterval(capture, 33);
    setInterval(interval);
  };

  const stopCapture = () => {
    clearInterval(intervalId);
    setIntervalId(null);
  };

  return (
    <div className="webcam-capture">
      <div className="webcam-container">
        <Webcam
          audio={false}
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          style={{ width: '100%', height: '100%' }}
        />
      </div>
      <div className="button-container">
        <button className="capture-button" onClick={startCapture}>
          Start Capture
        </button>
        <button className="stop-button" onClick={stopCapture}>
          Stop Capture
        </button>
      </div>
    </div>
  );
};

export default WebcamCapture;