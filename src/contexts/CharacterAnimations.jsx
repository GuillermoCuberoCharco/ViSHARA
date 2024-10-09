import { createContext, useContext, useEffect, useState } from "react";
import io from "socket.io-client";
export const CharacterAnimationsContext = createContext();

export const CharacterAnimationsProvider = (props) => {
  const [animationIndex, setAnimationIndex] = useState(0);
  const [animations, setAnimations] = useState([]);

  // Connect to the animation socket and control the animation interchanges
  useEffect(() => {
    const socket = io("ws://localhost:8081", {
      transports: ["websocket"],
      upgrade: false
    });

    socket.on("connect", () => {
      console.log("Animation socket connected");
    });

    const handleAnimationChange = (message) => {
      if (message.state) {
        const animationIndex = animations.findIndex((animation) => animation === message.state);
        if (animationIndex !== -1) {
          setAnimationIndex(animationIndex);
        }
      }

      if (message.emotions) {
        console.log("Emotions detected:", message.emotions);
      }
    };

    try {
      socket.on("watson_message", handleAnimationChange);
      socket.on("wizard_message", handleAnimationChange);
    } catch (error) {
      console.error("Invalid JSON", error);
    }

    return () => socket.close();
  }, [animations, setAnimationIndex]);


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