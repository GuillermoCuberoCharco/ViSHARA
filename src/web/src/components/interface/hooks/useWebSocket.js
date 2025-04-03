import { useEffect } from "react";
import io from "socket.io-client";
import { SERVER_URL } from "../../../config";

const useWebSocket = (handlers) => {
    const [socket, setSocket] = useState(null);

    useEffect(() => {
        const newSocket = io(SERVER_URL, {
            path: '/message-socket',
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 10000,
            forceNew: true
        });

        setSocket(newSocket);

        const setupEventListeners = () => {
            newSocket.on('connect', () => {
                console.log('Connected to server');
                newSocket.emit('register_client', 'web');
            });

            newSocket.on('registration_success', handlers.handleRegistrationSuccess);
            newSocket.on('robot_message', handlers.handleRobotMessage);
            newSocket.on('wizard_message', handlers.handleWizardMessage);
            newSocket.on('client_message', handlers.handleClientMessage);
            newSocket.on('connect_error', handlers.handleConnectError);
            newSocket.on('error', handlers.handleSocketError);

            newSocket.on('reconnect_attempt', (attemptNumber) => {
                console.log(`Reconnecting attempt ${attemptNumber}...`);
            });

            newSocket.on('reconnect_failed', () => {
                console.log('Reconnection failed');
                handlers.handleConnectError({ message: 'Reconnection failed after 5 attempts' })
            });
        };

        setupEventListeners();

        return () => {
            newSocket.offAny();
            newSocket.disconnect();
        };
    }, [handlers]);

    return socket;
};

export default useWebSocket;