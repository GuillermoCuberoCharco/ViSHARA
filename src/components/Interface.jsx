import axios from "axios";
import React, { useContext, useEffect, useRef, useState } from "react";
import { ReactMic } from "react-mic";
import '../InterfaceStyle.css';
import { CharacterAnimationsContext } from "../contexts/CharacterAnimations";
import CameraCapture from "./CameraCapture";

const Interface = () => {
  const { animations, setAnimationIndex } = useContext(CharacterAnimationsContext);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [isChatVisible, setChatVisible] = useState(true);
  const [socket, setSocket] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const lastMessageRef = useRef(null);
  const [audioSrc, setAudioSrc] = useState(null);

  const startRecording = () => {
    setIsRecording(true);
  };
  
  const stopRecording = () => {
    setIsRecording(false);
  };
  
  const onData = (recordedBlob) => {
    console.log('chunk of real-time data is: ', recordedBlob);
  }

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

//Llamada a la API de transcripción de voz de Google Cloud Speech-to-Text
  const handleTranscribe = async () => {
    try {
      const audio = await blobToBase64(recordedBlob.blob);
      const response = await axios.post("http://localhost:8082/transcribe", { audio });
      const transcript = response.data.transcript;
      setNewMessage(transcript);
    } catch (error) {
      console.error("Error transcribing", error);
    }
  };

//Llamada a la API de síntesis de voz de Google Cloud Text-to-Speech
  const handleSynthesize = async (message) => {
    const response = await axios.post("http://localhost:8082/synthesize", { text: message });
    const audioSrc = `data:audio/mp3;base64,${response.data.audioContent}`;
    setAudioSrc(audioSrc);
  };

  //Conexión con el servidor WebSocket
  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8081");

    socket.addEventListener("message", async (event) => {
      const command = await event.data.text();
      console.log("Mensaje recibido", command);

      if (command.startsWith("/")) {
        const message = command.slice(1);
        setMessages((prevMessages) => [...prevMessages, { text: message, sender: "them" }]);
        handleSynthesize(message);
      } else {
        const index = animations.findIndex((anim) => anim === animation);
        if (index !== -1) {
          setAnimationIndex(index);
        }
      }
    });

    setSocket(socket);
    return () =>{
      socket.close();
    }

  }, []);

  useEffect(() => {
    if (lastMessageRef.current){
      lastMessageRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const sendMessage = () => {
    if (socket && newMessage){
      setMessages((prevMessages) => [...prevMessages, { text: newMessage, sender: "me" }]);
      socket.send(newMessage);
      setNewMessage("");
    }
  };

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
        <CameraCapture />
        <audio src={audioSrc} autoPlay />
        <button onClick={isRecording ? stopRecording : startRecording}>
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>
        <ReactMic
          record={isRecording}
          className="sound-wave"
          onStop={onStop}
          onData={onData}
          strokeColor="#000000"
          backgroundColor="#FF4081" />
      </div>
    </div>
  );
};

export default Interface;