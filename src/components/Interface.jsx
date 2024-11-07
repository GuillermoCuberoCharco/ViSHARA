import axios from "axios";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { ReactMic } from "react-mic";
import { useCharacterAnimations } from "../contexts/CharacterAnimations";
import { socketService } from "../service/SocketService";
import '../styles/InterfaceStyle.css';
import { useVideo } from "./useVideo";

const Interface = () => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [isChatVisible, setChatVisible] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [audioSrc, setAudioSrc] = useState(null);
  const [faceDetected, setFaceDetected] = useState(false);
  const [isWaitingResponse, setIsWaitingResponse] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');

  const waitTimer = useRef(null);
  const lastMessageRef = useRef(null);
  const audioContext = useRef(null);
  const analyser = useRef(null);
  const dataArray = useRef(null);
  const silenceCounter = useRef(0);

  const { setAnimationIndex, animations } = useCharacterAnimations();

  // Logic to detect face and start recording
  const handleFaceDetected = (imageDataUrl) => {

    if (!isRecording && !isWaiting && !isWaitingResponse) {
      startRecording();

      if (!faceDetected) {
        const helloAnimationIndex = animations.findIndex((animation) => animation === "Hello");
        if (helloAnimationIndex !== -1) {
          setAnimationIndex(helloAnimationIndex);
          setFaceDetected(true);
        }
      }
    }
  };

  const { videoRef, canvasRef, videoStatus, frameSent, isModelLoaded } = useVideo(handleFaceDetected);

  // Create audio context and analyser for volume detection
  useEffect(() => {
    audioContext.current = new (window.AudioContext || window.webkitAudioContext)();
    analyser.current = audioContext.current.createAnalyser();
    analyser.current.fftSize = 256;
    dataArray.current = new Uint8Array(analyser.current.frequencyBinCount);

    return () => {
      if (audioContext.current) {
        audioContext.current.close();
      }
    };
  }, []);

  // Effect to scroll to the last message when a new message is added
  useEffect(() => {
    if (lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Connection to the WebSocket server for the chat
  useEffect(() => {
    const setupConnection = async () => {
      try {
        await socketService.connectMessageSocket();
        setConnectionStatus('Connected');

        socketService.addListener('watson_message', handleWatsonMessage);
        socketService.addListener('wizard_message', handleWizardMessage);
        socketService.addListener('client_message', handleClientMessage);
        socketService.addListener('connection', handleConnectionChange);
      } catch (error) {
        setConnectionStatus(`Connection error: ${error.message}`);
      }
    };

    setupConnection();

    return () => {
      socketService.disconnect();
      if (waitTimer.current) {
        clearTimeout(waitTimer.current);
      }
    };
  }, []);

  const handleWatsonMessage = useCallback((message) => {
    setMessages(prev => [...prev, { text: message.text, sender: "watson" }]);
    handleSynthesize(message.text);
    setAnimationIndex(message.state);
    setIsWaitingResponse(false);
  }, [setAnimationIndex]);

  const handleWizardMessage = useCallback((message) => {
    setMessages(prev => [...prev, { text: message.text, sender: "wizard" }]);
    handleSynthesize(message.text);
    setAnimationIndex(message.state);
    setIsWaitingResponse(false);
  }, [setAnimationIndex]);

  const handleClientMessage = useCallback((message) => {
    setMessages(prev => [...prev, { text: message.text, sender: "me" }]);
  }, []);

  const handleConnectionChange = useCallback((message) => {
    setConnectionStatus(status.status);
  }, []);

  const startRecording = () => {
    if (!isWaiting) {
      setIsRecording(true);
      silenceCounter.current = 0;
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    setIsWaiting(true);
    setIsWaitingResponse(true);

    // Wait 2 seconds after stopping the recording
    waitTimer.current = setTimeout(() => {
      setIsWaiting(false);
    }, 2000);
  };

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
        setIsWaitingResponse(false);
        silenceCounter.current = 0;
      }
    } else {
      silenceCounter.current = 0;
    }

    if (isRecording) {
      requestAnimationFrame(() => analyzeAudio(recordedBlob));
    }
  };

  const onStop = (recordedBlob) => {
    setRecordedBlob(recordedBlob);
    handleTranscribe();
  };

  // Send message to the server as a client message
  const sendMessage = useCallback(() => {
    if (newMessage.trim()) {
      const currentAnimation = animations[setAnimationIndex];
      const messageToSend = {
        type: "client_message",
        text: newMessage,
        state: currentAnimation
      };

      setMessages(prev => [...prev, { text: newMessage, sender: "me" }]);
      socketService.sendMessage(messageToSend);
      setNewMessage("");
      setIsWaitingResponse(true);
    }
  }, [newMessage, animations, setAnimationIndex]);

  // Endpoint call to the Google Cloud Speech-to-Text API
  const handleTranscribe = async () => {
    try {
      const audio = await blobToBase64(recordedBlob.blob);
      const response = await axios.post("http://localhost:8081/transcribe", { audio });
      const transcript = response.data.transcript;
      setNewMessage(transcript);
      sendMessage();
    } catch (error) {
      console.error("Error transcribing", error);
    }
  };

  // Endpoint call to the Google Cloud Text-to-Speech API
  const handleSynthesize = async (message) => {
    try {
      const response = await axios.post("http://localhost:8081/synthesize", { text: message });
      const audioSrc = `data:audio/mp3;base64,${response.data.audioContent}`;
      setAudioSrc(audioSrc);
    } catch (error) {
      console.error("Error synthesizing", error);
    }
  };



  useEffect(() => {
    if (recordedBlob) {
      handleTranscribe();
    }
  }, [recordedBlob]);

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

  const onData = (recordedBlob) => {
    if (isRecording) {
      analyzeAudio(recordedBlob);
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
    <div className={"chat-wrapper"}>
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
                <div className="message-content">
                  {message.text}
                </div>
                {message.sender !== "me" && (
                  <dic className="message-info">
                    {message.sender === "watson" ? "SHARA" : "Wizard"}
                  </dic>
                )}
              </div>
            ))}
          </div>
        </div>
        <div className="input-container">
          <textarea
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Escriba su mensaje..."
            className="input-field"
            disabled={isWaitingResponse}
          />
        </div>
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