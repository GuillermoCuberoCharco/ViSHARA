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
  const [isMobile, setIsMobile] = useState(false);

  const webSocketHandlers = {
    handleRegistrationSuccess: () => {
      console.log("Registration successful");
    },
    handleConnectError: (error) => {
      console.error("Connection error:", error);
    }
  };

  // Función para detectar dispositivos móviles
  const detectMobile = () => {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;

    // Detectar móviles por user agent
    const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i;
    const isMobileUA = mobileRegex.test(userAgent.toLowerCase());

    // Detectar por características de pantalla táctil y tamaño
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const isSmallScreen = window.innerWidth <= 768 || window.innerHeight <= 1024;

    return isMobileUA || (isTouchDevice && isSmallScreen);
  };

  const handleStreamReady = (stream) => {
    if (stream) {
      console.log("Stream ready in App component - Normal mode");
      setSharedStream(stream);
    } else {
      console.log("No stream available - Wizard mode enabled");
      setSharedStream(null);
      setIsWizardMode(true);
    }
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
        // Primero detectar si es móvil
        const mobileDevice = detectMobile();
        setIsMobile(mobileDevice);

        if (mobileDevice) {
          // En móviles: permitir la app normal pero sin embebido
          console.log("Dispositivo móvil detectado - App normal sin embebido");
          setIsStreamReady(true);
          setIsWizardMode(false);
          return;
        }

        // Para desktop: verificar disponibilidad de cámara
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          console.log("No hay soporte para cámara - Modo wizard activado");
          setIsWizardMode(true);
          setIsStreamReady(true);
          return;
        }

        const devices = await navigator.mediaDevices.enumerateDevices();
        const hasCamera = devices.some(device => device.kind === 'videoinput');

        if (!hasCamera) {
          console.log("No hay cámara disponible - Modo wizard activado");
          setIsWizardMode(true);
          setIsStreamReady(true);
        } else {
          console.log("Cámara disponible - Modo normal con embebido");
          setIsWizardMode(false);
        }
      } catch (error) {
        console.log("Error al detectar configuración, asumiendo modo wizard:", error);
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

  // Determinar si mostrar el componente de video embebido
  const shouldShowEmbeddedVideo = !isMobile && !isWizardMode;

  return (
    <WebSocketProvider handlers={webSocketHandlers}>
      <Canvas camera={{ position: [1.5, 1.5, 0.5], fov: 50 }} shadows>
        <Sky sunPosition={[100, -50, 100]} />
        <Experience
          animationIndex={animationIndex}
          setAnimations={setAnimations}
        />
      </Canvas>

      {/* Solo mostrar WebSocketVideoComponent en desktop con cámara */}
      {shouldShowEmbeddedVideo && (
        <WebSocketVideoComponent
          onStreamReady={handleStreamReady}
          onStreamError={handleStreamError}
        />
      )}

      {/* Mostrar UI cuando esté listo O sea móvil O sea wizard mode */}
      {(isStreamReady || isMobile || isWizardMode) && (
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