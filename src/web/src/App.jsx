import { Sky } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useEffect, useRef, useState } from "react";
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

  // Timeout para casos donde no se detecte contexto embebido pero falten servicios
  const videoTimeoutRef = useRef(null);
  const VIDEO_TIMEOUT = 10000; // 10 segundos como fallback

  const webSocketHandlers = {
    handleRegistrationSuccess: () => {
      console.log("Registration successful");
    },
    handleConnectError: (error) => {
      console.error("Connection error:", error);
    }
  };

  const handleStreamReady = (stream) => {
    // Limpiar timeout si el stream se establece correctamente
    if (videoTimeoutRef.current) {
      clearTimeout(videoTimeoutRef.current);
      videoTimeoutRef.current = null;
    }

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

    // Limpiar timeout si hay error explícito
    if (videoTimeoutRef.current) {
      clearTimeout(videoTimeoutRef.current);
      videoTimeoutRef.current = null;
    }

    setIsStreamReady(true);
    setIsWizardMode(true);
  };

  const activateWizardMode = (reason = "Embedded browser context detected") => {
    console.log(`Activating wizard mode: ${reason}`);
    setIsWizardMode(true);
    setIsStreamReady(true);
    setSharedStream(null);

    // Limpiar timeout si está activo
    if (videoTimeoutRef.current) {
      clearTimeout(videoTimeoutRef.current);
      videoTimeoutRef.current = null;
    }
  };

  const detectEmbeddedBrowser = () => {
    console.log("Detecting browser context...");

    // 1. Detectar User Agent de navegadores embebidos
    const userAgent = navigator.userAgent.toLowerCase();
    const isEmbedded =
      userAgent.includes('qtwebengine') ||           // PyQt6 WebEngine
      userAgent.includes('electron') ||              // Electron
      userAgent.includes('cef') ||                   // Chromium Embedded Framework
      userAgent.includes('webview') ||               // WebView genérico
      userAgent.includes('embedded') ||              // Indicador genérico
      window.location.protocol === 'file:' ||        // Cargado desde archivo local
      window.frameElement !== null;                  // Dentro de un iframe

    if (isEmbedded) {
      console.log(`Embedded browser detected via User Agent: ${userAgent}`);
      return true;
    }

    // 2. Detectar por APIs faltantes/restringidas
    const hasRestrictedAPIs =
      !navigator.mediaDevices ||                     // Sin MediaDevices API
      !navigator.mediaDevices.getUserMedia ||        // Sin getUserMedia
      !window.speechSynthesis ||                     // Sin Speech API
      typeof navigator.permissions === 'undefined';  // Sin Permissions API

    if (hasRestrictedAPIs) {
      console.log("Restricted APIs detected, likely embedded context");
      return true;
    }

    // 3. Detectar por contexto de ventana
    const hasRestrictedWindow =
      window.parent !== window ||                    // Dentro de frame
      window.top !== window ||                       // No es ventana top-level
      !window.chrome ||                              // Sin Chrome API (en navegadores embebidos)
      window.process;                                // Electron process object

    if (hasRestrictedWindow) {
      console.log("Restricted window context detected");
      return true;
    }

    // 4. Test específico para PyQt WebEngine
    try {
      // PyQt WebEngine tiene características específicas
      const isQtWebEngine =
        typeof window.qt !== 'undefined' ||          // Objeto Qt disponible
        navigator.userAgent.includes('Qt') ||        // Qt en User Agent
        typeof window.qwebchannel !== 'undefined';   // QWebChannel disponible

      if (isQtWebEngine) {
        console.log("PyQt WebEngine context detected");
        return true;
      }
    } catch (error) {
      console.log("Error checking Qt context:", error);
    }

    return false;
  };

  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Detectar inmediatamente si estamos en navegador embebido
        if (detectEmbeddedBrowser()) {
          activateWizardMode("Embedded browser context detected");
          return;
        }

        // Si no es navegador embebido, verificar disponibilidad de servicios
        console.log("Standard browser detected, checking service availability...");

        // Verificar si el navegador soporta acceso a dispositivos de media
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          console.log("MediaDevices not supported, enabling wizard mode");
          activateWizardMode("MediaDevices not supported");
          return;
        }

        // Test de permisos de cámara
        try {
          const devices = await navigator.mediaDevices.enumerateDevices();
          const hasCamera = devices.some(device => device.kind === 'videoinput');

          if (!hasCamera) {
            console.log("No camera devices found, enabling wizard mode");
            activateWizardMode("No camera devices found");
            return;
          }

          // Test de acceso real a la cámara (sin activarla)
          try {
            const testStream = await navigator.mediaDevices.getUserMedia({
              video: { width: 1, height: 1 },
              audio: false
            });

            // Si llegamos aquí, la cámara es accesible
            testStream.getTracks().forEach(track => track.stop());
            console.log("Camera access test successful, proceeding with normal mode");

            // Establecer timeout como fallback final
            videoTimeoutRef.current = setTimeout(() => {
              console.log("Video services timeout reached, activating wizard mode");
              activateWizardMode("Video services timeout");
            }, VIDEO_TIMEOUT);

          } catch (cameraError) {
            console.log("Camera access test failed:", cameraError.name, cameraError.message);
            activateWizardMode(`Camera access denied: ${cameraError.message}`);
            return;
          }

        } catch (deviceError) {
          console.log("Device enumeration failed:", deviceError);
          activateWizardMode(`Device access error: ${deviceError.message}`);
          return;
        }

      } catch (error) {
        console.log("Initialization error, enabling wizard mode:", error);
        activateWizardMode(`Initialization error: ${error.message}`);
      }
    };

    initializeApp();

    return () => {
      if (videoTimeoutRef.current) {
        clearTimeout(videoTimeoutRef.current);
      }
    };
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