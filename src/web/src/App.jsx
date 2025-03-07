import { Sky } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import React, { useState } from "react";
import Experience from "./components/experience/Experience";
import Interface from "./components/interface/Interface";
import WebSocketVideoComponent from "./components/WebSocketVideo";
import { CharacterAnimationsProvider } from "./contexts/CharacterAnimations";

function App() {
  const [sharedStream, setSharedStream] = useState(null);

  const handleStreamReady = (stream) => {
    setSharedStream(stream);
  };

  return (
    <CharacterAnimationsProvider>
      <Canvas camera={{ position: [1.5, 1.5, 0.5], fov: 50 }} shadows>
        <Sky sunPosition={[100, -50, 100]} />
        <Experience >
        </Experience>
      </Canvas>
      <WebSocketVideoComponent onStreamReady={handleStreamReady} />
      <Interface sharedStream={sharedStream} />
    </CharacterAnimationsProvider>
  );

}

export default App;
