import { createContext, useContext, useEffect, useState } from "react";
import io from "socket.io-client";
export const CharacterAnimationsContext = createContext();

export const CharacterAnimationsProvider = (props) => {
  const [animationIndex, setAnimationIndex] = useState(0);
  const [animations, setAnimations] = useState([]);
  const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:8081';

  // Connect to the animation socket and control the animation interchanges
  useEffect(() => {
    const socket = io(SERVER_URL, {
      path: "/message-socket",
      transports: ["websocket"],
      upgrade: false
    });

    socket.on("connect", () => {
      console.log("Animation socket connected");
      socket.emit("register_animation", { client: "animation" });
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