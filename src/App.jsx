import { Sky } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useEffect } from "react";
import Experience from "./components/Experience";
import Interface from "./components/Interface";
import { initializedWebRTC } from "./components/WebRTCService";
import { CharacterAnimationsProvider } from "./contexts/CharacterAnimations";

function App() {
  useEffect(() => {
    initializedWebRTC();
  }, []);

  return (
    <CharacterAnimationsProvider>
      <Canvas camera={{ position: [1.5, 1.5, 0.5], fov: 50 }} shadows>
        <Sky sunPosition={[100, -50, 100]} />
        <Experience >
        </Experience>
      </Canvas>
      <Interface />
    </CharacterAnimationsProvider>
  );
}

export default App;
