import { Sky } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import React, { useEffect, useState } from "react";
import Experience from "./components/experience/Experience";
import Interface from "./components/interface/Interface";
import WebSocketVideoComponent from "./components/WebSocketVideo";
import { WebSocketProvider } from "./contexts/WebSocketContext";

function App() {
  const [sharedStream, setSharedStream] = useState(null);
  const [isStreamReady, setIsStreamReady] = useState(false);
  const [animationIndex, setAnimationIndex] = useState(0);
  const [animations, setAnimations] = useState([]);

  const webSocketHandlers = {
    handleRegistrationSuccess: () => {
      console.log("Registration successful");
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
      <Canvas camera={{ position: [1.5, 1.5, 0.5], fov: 50 }} shadows>
        <Sky sunPosition={[100, -50, 100]} />
        <Experience
          animationIndex={animationIndex}
          setAnimations={setAnimations}
        />
      </Canvas>
      <WebSocketVideoComponent onStreamReady={handleStreamReady} />
      {isStreamReady && (
        <Interface
          sharedStream={sharedStream}
          animationIndex={animationIndex}
          setAnimationIndex={setAnimationIndex}
          animations={animations}
        />
      )}
    </WebSocketProvider>
  );

}

export default App;
