import { Sky } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import React, { useEffect, useState } from "react";
import Experience from "./components/experience/Experience";
import Interface from "./components/interface/Interface";
import WebSocketVideoComponent from "./components/WebSocketVideo";
import { CharacterAnimationsProvider } from "./contexts/CharacterAnimations";
import { WebSocketProvider } from "./contexts/WebSocketContext";

function App() {
  const [sharedStream, setSharedStream] = useState(null);
  const [isStreamReady, setIsStreamReady] = useState(false);

  const webSocketHandlers = {
    handleRegistrationSuccess: (data) => {
      console.log("Registration successful:", data);
    },
    handleConnectError: (error) => {
      console.error("Connection error:", error);
    }
  };

  const handleStreamReady = (stream) => {
    console.log("Stream ready in App component");
    setSharedStream(stream);
    setIsStreamReady(true);
  };

  useEffect(() => {
    if (sharedStream) {
      console.log("Shared stream is now available for other components");
    }
  }, [sharedStream]);

  return (
    <WebSocketProvider handlers={webSocketHandlers}>
      <CharacterAnimationsProvider>
        <Canvas camera={{ position: [1.5, 1.5, 0.5], fov: 50 }} shadows>
          <Sky sunPosition={[100, -50, 100]} />
          <Experience />
        </Canvas>
        <WebSocketVideoComponent onStreamReady={handleStreamReady} />
        {isStreamReady && <Interface sharedStream={sharedStream} />}
      </CharacterAnimationsProvider>
    </WebSocketProvider>
  );

}

export default App;
