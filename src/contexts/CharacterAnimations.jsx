import { createContext, useContext, useEffect, useState } from "react";

export const CharacterAnimationsContext = createContext();


export const CharacterAnimationsProvider = (props) => {
  const [animationIndex, setAnimationIndex] = useState(0);
  const [animations, setAnimations] = useState([]);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8081");

    socket.onopen = () => console.log("Me he conectado al WebSocket");
    socket.onmessage = async (event) => {
      const message = await event.data.text();
      console.log("Mensaje recibido", message);

      if (animations.includes(message)) {
        const index = animations.findIndex(
           (animation) => animation === message
        );
        if (index !== -1) {
          setAnimationIndex(index);
        }
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