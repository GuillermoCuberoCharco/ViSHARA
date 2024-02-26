import axios from "axios";
import React, { useContext, useEffect, useRef, useState } from "react";
import '../InterfaceStyle.css';
import { CharacterAnimationsContext } from "../contexts/CharacterAnimations";

const Interface = () => {
  const { animations, setAnimationIndex } = useContext(CharacterAnimationsContext);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [socket, setSocket] = useState(null);
  const lastMessageRef = useRef(null);

  const [audioSrc, setAudioSrc] = useState(null);

  const handleSynthesize = async (message) => {
      const response = await axios.post("http://localhost:8082/synthesize", { text: message });
      const audioSrc = `data:audio/mp3;base64,${response.data.audioContent}`;
      setAudioSrc(audioSrc);
    };

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
    if (socket){
      setMessages((prevMessages) => [...prevMessages, { text: newMessage, sender: "me" }]);
      socket.send(newMessage);
      setNewMessage("");
    }
  };

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
      </div>
      <audio src={audioSrc} autoPlay />
    </div>
  );
};

export default Interface;