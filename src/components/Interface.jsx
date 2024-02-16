import React, { useContext, useEffect, useRef, useState } from "react";
import '../InterfaceStyle.css';
import { CharacterAnimationsContext } from "../contexts/CharacterAnimations";

const Interface = () => {
  const { animations, setAnimationIndex } = useContext(CharacterAnimationsContext);
  const [messages, setMessages] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [newMessage, setNewMessage] = useState("");
  const [socket, setSocket] = useState(null);
  const lastMessageRef = useRef(null);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8081");

    socket.addEventListener("message", async (event) => {
      const command = await event.data.text();
      console.log("Mensaje recibido", command);

      if (command.startsWith("/")) {
        const message = command.slice(1);
        setMessages((prevMessages) => [...prevMessages, { text: message, sender: "them" }]);
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
    if (socket){
      setMessages((prevMessages) => [...prevMessages, { text: newMessage, sender: "me" }]);
      socket.send(newMessage);
      setNewMessage("");
    }
  };

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
 
    if (!SpeechRecognition){
      console.log("El navegador no soporta el reconocimiento de voz");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "es-ES";

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setNewMessage(transcript);
    };

    recognition.onend = () => {
      console.log("Fin del reconocimiento de voz");
      setIsListening(false);
    };

    const startListening = () => {
      setIsListening(true);
      recognition.start();
    };

    const stopListening = () => {
      setIsListening(false);
      recognition.stop();
    };

    const toggleListening = () => {
      if (isListening) {
        stopListening();
      } else {
        startListening();
      }
    };

    const listenButton = document.querySelector('#listen-btn');
    if (listenButton){
      listenButton.addEventListener("click", toggleListening);
    }

    return () => {
      if (listenButton){
        listenButton.removeEventListener("click", toggleListening);
      }
    };
  }, [isListening, sendMessage]);

  return (
    <div className="chat-container">
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
        <button id="listen-btn" className="mic.button">
          {isListening ? (
            <i className="fas fa-microphone-slash"></i>
          ) : (
            <i className="fas fa-microphone"></i>
          )}
            </button>
      </div>
    </div>
  );
};

export default Interface;