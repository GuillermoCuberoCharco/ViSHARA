import { createContext, useContext, useEffect, useState } from "react";

export const CharacterAnimationsContext = createContext();


export const CharacterAnimationsProvider = (props) => {
  const [animationIndex, setAnimationIndex] = useState(0);
  const [animations, setAnimations] = useState([]);
  const [currentMessage, setCurrentMessage] = useState("");

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8081");

    socket.onopen = () => console.log("Me he conectado al WebSocket");
    socket.onmessage = (event) => {
      try {
        const messageData = JSON.parse(event.data);
        console.log("Message received", messageData);
        if (messageData.type === "wizard_message") {
          const newAnimation = messageData.state;
          if (animations.includes(newAnimation)) {
            const index = animations.findIndex(
              (animation) => animation === newAnimation
            );
            if (index !== -1) {
              setAnimationIndex(index);
            }
          }
        }
      } catch (error) {
        console.error("Invalid JSON", error);
      }
    };

    return () => socket.close();
  }, [animations]);


  return (
    <CharacterAnimationsContext.Provider
      value={{
        animationIndex,
        setAnimationIndex,
        animations,
        setAnimations
      }}
    >
      {props.children}
    </CharacterAnimationsContext.Provider>
  );
};

export const useCharacterAnimations = () => useContext(CharacterAnimationsContext);