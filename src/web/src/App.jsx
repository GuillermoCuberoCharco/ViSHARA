import { Sky } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useEffect, useState } from "react";
import Experience from "./components/experience/Experience";
import UI from "./components/UI/UI";
import WebSocketVideoComponent from "./components/WebSocketVideo";
import { WebSocketProvider } from "./contexts/WebSocketContext";

function App() {
  const [sharedStream, setSharedStream] = useState(null);
  const [isStreamReady, setIsStreamReady] = useState(false);
  const [animationIndex, setAnimationIndex] = useState(0);
  const [animations, setAnimations] = useState([]);
  const [isWizardMode, setIsWizardMode] = useState(false);

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

  const handleStreamError = (error) => {
    console.error("Stream error in App component, assuming wizard mode:", error);
    setIsStreamReady(true);
    setIsWizardMode(true);
  };

  useEffect(() => {
    const detectWizardMode = async () => {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          setIsWizardMode(true);
          setIsStreamReady(true);
          return;
        }

        const devices = await navigator.mediaDevices.enumerateDevices();
        const hasCamera = devices.some(device => device.kind === 'videoinput');

        if (!hasCamera) {
          setIsWizardMode(true);
          setIsStreamReady(true);
        }
      } catch (error) {
        console.log("Camera access not available, enabling wizard mode");
        setIsWizardMode(true);
        setIsStreamReady(true);
      }
    };

    detectWizardMode();
  }, []);

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
      {!isWizardMode && (
        <WebSocketVideoComponent
          onStreamReady={handleStreamReady}
          onStreamError={handleStreamError}
        />
      )}
      {(isStreamReady || isWizardMode) && (
        <UI
          sharedStream={sharedStream}
          animationIndex={animationIndex}
          setAnimationIndex={setAnimationIndex}
          animations={animations}
          isWizardMode={isWizardMode}
        />
      )}
    </WebSocketProvider>
  );

}

export default App;
