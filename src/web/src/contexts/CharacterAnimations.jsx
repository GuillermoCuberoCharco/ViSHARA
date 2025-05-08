import { createContext, useContext, useEffect, useState } from "react";
import io from "socket.io-client";
import { ANIMATION_MAPPINGS, SERVER_URL } from "../config";
export const CharacterAnimationsContext = createContext();

export const CharacterAnimationsProvider = (props) => {
  const [animationIndex, setAnimationIndex] = useState(0);
  const [animations, setAnimations] = useState([]);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const newSocket = io(SERVER_URL, {
      path: "/animation-socket",
      transports: ["websocket"],
      upgrade: false
    });

    newSocket.on("connect", () => {
      newSocket.emit("register_animation", { client: "animation" });
    });

    setSocket(newSocket);
    return () => newSocket.close();
  }, []);

  useEffect(() => {
    if (!socket || animations.length === 0) return;

    const handleAnimationChange = (message) => {
      if (message && message.state) {
        console.log("Received animation state:", message.state);
        const animationName = ANIMATION_MAPPINGS[message.state] || "Attention";
        const index = animations.findIndex((animation) => animation === animationName);

        if (index !== -1) {
          setAnimationIndex(index);
        }
      }
    };

    socket.on("animation_state", handleAnimationChange);

    return () => {
      socket.off("animation_state", handleAnimationChange);
    };
  }, [socket, animations]);

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