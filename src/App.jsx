import { Sky } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import Experience from "./components/Experience";
import Interface from "./components/Interface";
import { CharacterAnimationsProvider } from "./contexts/CharacterAnimations";

function App() {
  return (
    <CharacterAnimationsProvider>
      <Canvas camera={{ position: [150, 150, 0.5], fov: 50 }} shadows>
        <Sky sunPosition={[100, -50, 100]} />
        <Experience >
        </Experience>
      </Canvas>
      <Interface />
    </CharacterAnimationsProvider>
  );
}

export default App;
