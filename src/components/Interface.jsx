import axios from "axios";
import React, { useEffect, useRef, useState } from "react";
import { ReactMic } from "react-mic";
import { useCharacterAnimations } from "../contexts/CharacterAnimations";
import '../InterfaceStyle.css';
import CameraCapture from "./CameraCapture";

const Interface = () => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [isChatVisible, setChatVisible] = useState(true);
  const [socket, setSocket] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const waitTimer = useRef(null);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const lastMessageRef = useRef(null);
  const [audioSrc, setAudioSrc] = useState(null);
  const audioContext = useRef(null);
  const analyser = useRef(null);
  const dataArray = useRef(null);
  const silenceCounter = useRef(0);
  const [faceDetected, setFaceDetected] = useState(false);
  const [isWaitingResponse, setIsWaitingResponse] = useState(false);
  const { setAnimationIndex, animations } = useCharacterAnimations();

  const startRecording = () => {
    if (!isWaiting && !isWaitingResponse) {
      setIsRecording(true);
      silenceCounter.current = 0;
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    setFaceDetected(false);
    setIsWaiting(true);
    setIsWaitingResponse(true);

    // Wait 2 seconds after stopping the recording
    waitTimer.current = setTimeout(() => {
      setIsWaiting(false);
    }, 2000);
  };

  // Effect to scroll to the last message when a new message is added
  useEffect(() => {
    if (lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Send message to the server as a client message
  const sendMessage = () => {
    if (socket && socket.readyState === WebSocket.OPEN && newMessage) {
      const currentAnimation = animations[setAnimationIndex];
      const messageObject = {
        type: "client_message",
        text: newMessage,
        state: currentAnimation
      };
      setMessages((prevMessages) => [...prevMessages, { text: newMessage, sender: "me" }]);
      socket.send(JSON.stringify(messageObject));
      setNewMessage("");
      setIsWaitingResponse(true);
    }
  };

  // Create audio context and analyser for volume detection
  useEffect(() => {
    audioContext.current = new (window.AudioContext || window.webkitAudioContext)();
    analyser.current = audioContext.current.createAnalyser();
    analyser.current.fftSize = 256;
    dataArray.current = new Uint8Array(analyser.current.frequencyBinCount);
  }, []);

  const onData = (recordedBlob) => {
    analyzeAudio(recordedBlob);
  }

  // Analyze audio volume in order to stop recording when silent
  const analyzeAudio = (recordedBlob) => {
    if (!audioContext.current || !analyser.current || !dataArray.current) return;

    analyser.current.getByteFrequencyData(dataArray.current);
    const volume = dataArray.current.reduce((sum, value) => sum + value, 0) / dataArray.current.length;

    const silenceThreshold = 20;
    const silenceDuration = 2000;

    if (volume < silenceThreshold) {
      silenceCounter.current += 1;
      if (silenceCounter.current > (silenceDuration / 50)) {
        stopRecording();
        silenceCounter.current = 0;
      }
    } else {
      silenceCounter.current = 0;
    }

    if (isRecording) {
      requestAnimationFrame(() => analyzeAudio(recordedBlob));
    }
  };

  useEffect(() => {
    if (recordedBlob) {
      handleTranscribe();
    }
  }, [recordedBlob]);

  const onStop = (recordedBlob) => {
    setRecordedBlob(recordedBlob);
    handleTranscribe();
  };

  const blobToBase64 = (blob) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = reject;
      reader.onload = () => {
        resolve(reader.result.split(",")[1]);
      };
      reader.readAsDataURL(blob);
    });
  };

  // Endpoint call to the Google Cloud Speech-to-Text API
  const handleTranscribe = async () => {
    try {
      const audio = await blobToBase64(recordedBlob.blob);
      const response = await axios.post("http://localhost:8082/transcribe", { audio });
      const transcript = response.data.transcript;
      setNewMessage(transcript);
      sendMessage();
    } catch (error) {
      console.error("Error transcribing", error);
    }
  };

  // Endpoint call to the Google Cloud Text-to-Speech API
  const handleSynthesize = async (message) => {
    const response = await axios.post("http://localhost:8082/synthesize", { text: message });
    const audioSrc = `data:audio/mp3;base64,${response.data.audioContent}`;
    setAudioSrc(audioSrc);
  };

  // Connection to the WebSocket server for messages exchange
  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8081");

    socket.addEventListener("message", (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (error) {
        console.error("Invalid JSON", error);
        return;
      }

      console.log("Message received", data);

      if (data.type === "watson_response" || data.type === "wizard_message") {
        setMessages((prevMessages) => [...prevMessages, { text: data.text, sender: "them" }]);
        handleSynthesize(data.text);
        setIsWaitingResponse(false);

        if (data.emotion) {
          console.log("Emotion detected", data.emotion);
        }
        if (data.mood) {
          console.log("Mood detected", data.mood);
        }
      }
    });

    setSocket(socket);
    return () => {
      socket.close();
    }

  }, []);

  // Logic to detect face and start recording
  const handleFaceDetected = (imageDataUrl) => {
    setFaceDetected(true);
    if (!isRecording && !isWaiting && !isWaitingResponse) {
      startRecording();

      const helloAnimationIndex = animations.findIndex((animation) => animation === "Hello");
      if (helloAnimationIndex !== -1) {
        setAnimationIndex(helloAnimationIndex);
      }
    }
  };

  // Cleanup the timer when the component unmounts
  useEffect(() => {
    return () => {
      if (waitTimer.current) {
        clearTimeout(waitTimer.current);
      }
    };
  }, []);

  return (
    <div className="chat-wrapper">
      <button className="toggle-chat-button" onClick={() => setChatVisible(!isChatVisible)}>
        {isChatVisible ? <i className="fas fa-arrow-left"></i> : <i className="fas fa-arrow-right"></i>}
      </button>
      <div className={`chat-container ${isChatVisible ? 'visible' : 'hidden'}`}>
        <div className="messages-container">
          <div className="messages-wrapper">
            {messages.map((message, index) => (
              <div
                key={index}
                ref={index === messages.length - 1 ? lastMessageRef : null}
                className={`message ${message.sender}`}
              >
                {message.text}
              </div>
            ))}
          </div>
        </div>
        <div className="input-container">
          <textarea
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                sendMessage();
                e.preventDefault();
              }
            }}
            className="input-field"
          />
        </div>
        <CameraCapture onFaceDetected={handleFaceDetected} />
        <audio src={audioSrc} autoPlay />
        <ReactMic
          record={isRecording}
          className="sound-wave"
          onStop={onStop}
          onData={onData}
          strokeColor="#000000"
          backgroundColor="#FF4081"
          mimeType="audio/webm"
          bufferSize={2048}
          sampleRate={44100} />
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isWaitingResponse}
        >
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>
      </div>
    </div>
  );
};

export default Interface;