import { createContext, useContext, useEffect, useState } from "react";
import io from "socket.io-client";
import { SERVER_URL } from "../config";
export const CharacterAnimationsContext = createContext();

export const CharacterAnimationsProvider = (props) => {
  const [animationIndex, setAnimationIndex] = useState(0);
  const [animations, setAnimations] = useState([]);

  // Connect to the animation socket and control the animation interchanges
  useEffect(() => {
    const socket = io(SERVER_URL, {
      path: "/animation-socket",
      transports: ["websocket"],
      upgrade: false
    });

    socket.on("connect", () => {
      console.log("Animation socket connected");
      socket.emit("register_animation", { client: "animation" });
    });

    const handleAnimationChange = (message) => {
      console.log("Received animation message:", message.state);
      if (message.state) {
        const animationName = ANIMATION_MAPPINGS[message.state] || "Attention";
        const animationIndex = animations.findIndex((animation) => animation === animationName);
        if (animationIndex !== -1) {
          setAnimationIndex(animationIndex);
        }
      }
    };

    try {
      socket.on("animation_state", handleAnimationChange);
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