import axios from "axios";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { ReactMic } from "react-mic";
import io from "socket.io-client";
import { useCharacterAnimations } from "../contexts/CharacterAnimations";
import StatusBar from "../contexts/StatusBar";
import '../styles/InterfaceStyle.css';
import FaceDetection from "./FaceDetection";

const Interface = ({ sharedStream }) => {
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
  const volumeCheckInterval = useRef(null);
  const analyser = useRef(null);
  const dataArray = useRef(null);
  const silenceCounter = useRef(0);
  const [faceDetected, setFaceDetected] = useState(false);
  const [isUserRecognized, setIsUserRecognized] = useState(false);
  const [recognizedUser, setRecognizedUser] = useState(null);
  const [isWaitingResponse, setIsWaitingResponse] = useState(false);
  const { setAnimationIndex, animations } = useCharacterAnimations();
  const [isRegistered, setIsRegistered] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8081';

  const startRecording = async () => {
    if (!isWaiting && !isSpeaking && !isWaitingResponse && isUserRecognized) {
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

  // Effect to scroll to the last message when a new message is added

  const scrollToBottom = () => {
    if (lastMessageRef.current) {
      lastMessageRef.current.scrollTop = lastMessageRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    if (messages.length > 0 && messages[messages.length - 1]?.text?.trim()) {
      scrollToBottom();
    }
  }, [messages]);

  // Send message to the server as a client message
  const sendMessage = useCallback(async () => {
    if (socket && newMessage && isRegistered) {
      const currentAnimation = animations[setAnimationIndex];
      const messageObject = {
        type: "client_message",
        text: newMessage,
        state: currentAnimation
      };
      socket.emit('message', messageObject);
      setNewMessage("");
      setIsWaitingResponse(true);
    } else if (!isRegistered) {
      console.error("Client not registered: cannot send message");
      setConnectionError("Client not registered");
    }
  }, [socket, newMessage, animations, setAnimationIndex]);

  const checkMicrophonePermission = async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log("Microphone permission granted");
      return true;
    } catch (error) {
      console.error("Microphone permission denied", error);
      if (!window.isSecureContext) {
        console.error("The app must be served over HTTPS to use the microphone");
      }
      return false;
    }
  };

  useEffect(() => {
    checkMicrophonePermission();
  }, []);

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

  useEffect(() => {
    if (recordedBlob && recordedBlob.blob) {
      handleTranscribe(recordedBlob);
    }
  }, [recordedBlob]);

  const onStop = async (recordedBlob) => {
    setRecordedBlob(recordedBlob);
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

  // Connection to the WebSocket server with SocketIo for messages exchange
  useEffect(() => {
    const newSocket = io(SERVER_URL, {
      transports: ['polling', 'websocket']
    });

    newSocket.io.on("upgrade", (transport) => {
      console.log("Upgraded to:", transport.name);
    });

    newSocket.on("connect_error", (error) => {
      console.error("Connection error", error);
      setConnectionError(error);
      setIsRegistered(false);
    });

    newSocket.on("error", (error) => {
      console.error("Error", error);
    });

    newSocket.on("connect", () => {
      console.log("Connected to server, attempting to register");
      newSocket.emit("register_client", "web");
    });

    newSocket.on("registration_success", (data) => {
      console.log("Registration successful", data);
      setIsRegistered(true);
      setConnectionError(null);
    });

    newSocket.on("disconnect", () => {
      console.log("Disconnected from server");
    });

    newSocket.on("watson_message", async (message) => {
      console.log("Received Watson message:", message);
      setMessages((messages) => [...messages, { text: message.text, sender: "watson" }]);
      await handleSynthesize(message.text);
      setIsWaitingResponse(false);

      if (message.emotions) {
        console.log("Emotions detected:", message.emotions);
      }
    });

    newSocket.on("wizard_message", async (message) => {
      console.log("Received Wizard message:", message);
      setMessages((messages) => [...messages, { text: message.text, sender: "wizard" }]);
      await handleSynthesize(message.text);
      setIsWaitingResponse(false);

      if (message.emotions) {
        console.log("Emotions detected:", message.emotions);
      }
    });

    newSocket.on('client_message', (data) => {
      console.log("Client message received", data);
      const messageText = data.text?.trim();
      if (messageText) {
        setMessages((prevMessages) => [...prevMessages, { text: data.text, sender: "me" }]);
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, []);

  // Logic to detect face and start recording
  const handleFaceDetected = () => {
    if (!faceDetected) {
      setFaceDetected(true);
      console.log("Face detected, waiting for recognition...");
    }
  };

  // Logic to for the recognition of the face
  const handleFaceRecognized = (userData) => {
    if (!isUserRecognized) {
      setIsUserRecognized(true);
      setRecognizedUser(userData);
      setCurrentUser(userData);
      setMessages(messages => [...messages, {
        text: `¡Bienvenido/a ${userData.label}! Te he reconocido y registrado en el sistema.`,
        sender: "system"
      }]);

      if (!isRecording && !isWaiting && !isWaitingResponse && !isSpeaking) {
        startRecording();

        const helloAnimationIndex = animations.findIndex((animation) => animation === "Hello");
        if (helloAnimationIndex !== -1) {
          setAnimationIndex(helloAnimationIndex);
        }
      }
    }
  };

  const handleNewFaceDetected = async (userData) => {
    console.log("New user registered:", userData);
    setIsUserRecognized(true);
    setRecognizedUser(userData);
    setCurrentUser(userData);

    setMessages(messages => [...messages, {
      text: `¡Bienvenido/a ${userData.label}! Es la primera vez que te veo, te he registrado en el sistema.`,
      sender: "system"
    }]);

    if (socket && isRegistered) {
      socket.emit('new_user_registered', userData);
    }

    if (!isRecording && !isWaiting && !isWaitingResponse && !isSpeaking) {
      startRecording();

      const helloAnimationIndex = animations.findIndex((animation) => animation === "Hello");
      if (helloAnimationIndex !== -1) {
        setAnimationIndex(helloAnimationIndex);
      }
    }
  };

  // Endpoint call to the Google Cloud Speech-to-Text API
  const handleTranscribe = async (blob) => {
    try {
      if (!blob || !blob.blob) {
        console.error("No blob to transcribe");
        return;
      }
      const audio = await blobToBase64(blob.blob);
      await axios.post(`${SERVER_URL}/transcribe`, {
        audio: audio,
        state: animations[setAnimationIndex]
      });
      setIsWaitingResponse(true);
    } catch (error) {
      console.error("Error transcribing", error);
      setIsWaitingResponse(false);
    }
  };

  // Endpoint call to the Google Cloud Text-to-Speech API
  const handleSynthesize = async (message) => {
    if (!message || message.trim() === '') {
      setIsSpeaking(false);
      setIsWaitingResponse(false);
      return;
    }
    setIsSpeaking(true);
    const response = await axios.post(`${SERVER_URL}/synthesize`, { text: message });
    const audioSrc = `data:audio/mp3;base64,${response.data.audioContent}`;
    setAudioSrc(audioSrc);
  };

  useEffect(() => {
    const audioElement = document.querySelector('audio');
    if (audioElement) {
      audioElement.onended = () => {
        setIsSpeaking(false);
      };
    }
  }, [audioSrc]);

  // Cleanup the timer when the component unmounts
  useEffect(() => {
    return () => {
      if (waitTimer.current) {
        clearTimeout(waitTimer.current);
      }
      if (volumeCheckInterval.current) {
        clearInterval(volumeCheckInterval.current);
      }
    };
  }, []);

  return (
    <div className={"chat-wrapper"}>
      <button className="toggle-chat-button" onClick={() => setChatVisible(!isChatVisible)}>
        {isChatVisible ? <i className="fas fa-arrow-left"></i> : <i className="fas fa-arrow-right"></i>}
      </button>
      <div className={`chat-container ${isChatVisible ? 'visible' : 'hidden'}`}>

        <div className="messages-container" ref={lastMessageRef}>
          <div className="messages-wrapper">
            {messages.map((message, index) => (
              <div
                key={index}
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
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (newMessage.trim()) {
                  sendMessage();
                }

              }
            }}
            className="input-field"
          />
        </div>
        <StatusBar
          isRecording={isRecording}
          isWaiting={isWaiting}
          isWaitingResponse={isWaitingResponse}
          audioSrc={audioSrc}
          isRegistered={isRegistered}
          connectionError={connectionError}
        />
        <FaceDetection
          onFaceDetected={handleFaceDetected}
          onFaceRecognized={handleFaceRecognized}
          onNewFaceDetected={handleNewFaceDetected}
          stream={sharedStream}
        />
        <audio src={audioSrc} autoPlay />
        <ReactMic
          record={isRecording}
          className="sound-wave"
          onStop={onStop}
          onData={onData}
          strokeColor="#000000"
          backgroundColor="#FF4081"
          mimeType="audio/webm"
          onError={(error) => console.error("ReactMic error:", error)}
          bufferSize={2048}
          sampleRate={44100}
          channelCount={1}
          visualSetting="sinewave"

        />
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